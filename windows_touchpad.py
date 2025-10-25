#!/usr/bin/env python3
"""
Windows Precision Touchpad Backend

Provides touchpad input capture for Windows using Windows Pointer Input API.
Compatible interface with Linux evdev backend.
"""

import platform
import time
import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Tuple
from ctypes import windll, Structure, POINTER, c_int, c_uint, byref, c_void_p
from ctypes.wintypes import DWORD, HWND, UINT, WPARAM, LPARAM, POINT, RECT, BOOL

# Check if we're on Windows
IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    try:
        import win32api
        import win32con
        import win32gui
        import threading
    except ImportError:
        print("⚠️  pywin32 not installed. Install with: pip install pywin32")
        IS_WINDOWS = False

# Windows Pointer Input API Constants
WM_POINTERDOWN = 0x0246
WM_POINTERUP = 0x0247
WM_POINTERUPDATE = 0x0245
WM_POINTERENTER = 0x0249
WM_POINTERLEAVE = 0x024A

PT_POINTER = 0x00000001
PT_TOUCH = 0x00000002
PT_PEN = 0x00000003
PT_MOUSE = 0x00000004
PT_TOUCHPAD = 0x00000005

POINTER_FLAG_NONE = 0x00000000
POINTER_FLAG_NEW = 0x00000001
POINTER_FLAG_INRANGE = 0x00000002
POINTER_FLAG_INCONTACT = 0x00000004
POINTER_FLAG_FIRSTBUTTON = 0x00000010
POINTER_FLAG_SECONDBUTTON = 0x00000020
POINTER_FLAG_THIRDBUTTON = 0x00000040
POINTER_FLAG_PRIMARY = 0x00002000
POINTER_FLAG_CONFIDENCE = 0x00004000
POINTER_FLAG_CANCELED = 0x00008000
POINTER_FLAG_DOWN = 0x00010000
POINTER_FLAG_UPDATE = 0x00020000
POINTER_FLAG_UP = 0x00040000

# Pointer structures
class POINTER_INFO(Structure):
    _fields_ = [
        ("pointerType", c_uint),
        ("pointerId", c_uint),
        ("frameId", c_uint),
        ("pointerFlags", c_uint),
        ("sourceDevice", c_void_p),
        ("hwndTarget", HWND),
        ("ptPixelLocation", POINT),
        ("ptHimetricLocation", POINT),
        ("ptPixelLocationRaw", POINT),
        ("ptHimetricLocationRaw", POINT),
        ("dwTime", DWORD),
        ("historyCount", c_uint),
        ("InputData", c_int),
        ("dwKeyStates", DWORD),
        ("PerformanceCount", c_uint),
        ("ButtonChangeType", c_uint),
    ]


@dataclass
class TouchPoint:
    """Single touch point with position and timing"""
    x: float
    y: float
    timestamp: float
    timestamp_ns: int


class WindowsTouchpadCapture:
    """
    Windows Precision Touchpad capture using Windows Pointer Input API
    
    Compatible interface with Linux TrackpadCapture
    """
    
    def __init__(self):
        if not IS_WINDOWS:
            raise RuntimeError("WindowsTouchpadCapture only works on Windows")
        
        self.screen_width = 1200
        self.screen_height = 800
        
        # Touch tracking
        self.active_touches: Dict[int, List[TouchPoint]] = {}
        self.completed_touches: List[List[TouchPoint]] = []
        self.is_capturing = False
        
        # Window handle for pointer messages
        self.hwnd = None
        self.pointer_enabled = False
        
        # Message loop thread
        self.message_thread = None
        self.running = False
        
        # Callbacks
        self.on_finger_down_callback = None
        self.on_finger_up_callback = None
        self.on_point_added_callback = None
        
        # Load user32.dll functions
        try:
            self.user32 = windll.user32
            
            # GetPointerInfo
            self.GetPointerInfo = self.user32.GetPointerInfo
            self.GetPointerInfo.argtypes = [c_uint, POINTER(POINTER_INFO)]
            self.GetPointerInfo.restype = BOOL
            
            # EnableMouseInPointer
            if hasattr(self.user32, 'EnableMouseInPointer'):
                self.EnableMouseInPointer = self.user32.EnableMouseInPointer
                self.EnableMouseInPointer.argtypes = [BOOL]
                self.EnableMouseInPointer.restype = BOOL
            else:
                self.EnableMouseInPointer = None
            
        except Exception as e:
            print(f"⚠️  Error loading Pointer Input API: {e}")
            self.user32 = None
    
    def open_device(self) -> bool:
        """Initialize Windows Pointer Input with capability checks"""
        try:
            if self.user32 is None:
                print(f"✗ Windows Pointer Input API not available")
                return False
            
            # Check for Precision Touchpad in registry
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\PrecisionTouchPad",
                    0,
                    winreg.KEY_READ
                )
                winreg.CloseKey(key)
                has_precision_touchpad = True
            except:
                has_precision_touchpad = False
            
            if not has_precision_touchpad:
                print(f"⚠️  Windows Precision Touchpad not detected in registry")
                print(f"  This may still work if you have a compatible touchpad")
            else:
                print(f"✓ Windows Precision Touchpad detected")
            
            # Create hidden window for receiving pointer messages
            self._create_message_window()
            
            if self.hwnd is None:
                print(f"✗ Failed to create message window")
                return False
            
            print(f"✓ Windows Pointer Input initialized")
            print(f"  Using WM_POINTER messages for multi-touch")
            print(f"  Window handle: 0x{self.hwnd:08X}")
            print(f"")
            print(f"⚠️  IMPORTANT: Touch the touchpad to generate events")
            
            self.pointer_enabled = True
            
            # Start message loop in background thread
            self.running = True
            self.message_thread = threading.Thread(target=self._message_loop, daemon=True)
            self.message_thread.start()
            
            return True
            
        except Exception as e:
            print(f"✗ Error initializing Pointer Input: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_message_window(self):
        """Create a hidden window to receive pointer messages"""
        try:
            # Register window class
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self._wnd_proc
            wc.lpszClassName = "TouchpadCaptureWindow"
            wc.hInstance = win32api.GetModuleHandle(None)
            
            try:
                class_atom = win32gui.RegisterClass(wc)
            except Exception:
                # Class might already be registered
                class_atom = win32gui.WNDCLASS()
            
            # Create window
            self.hwnd = win32gui.CreateWindow(
                "TouchpadCaptureWindow",
                "Touchpad Capture",
                win32con.WS_OVERLAPPEDWINDOW,
                0, 0, self.screen_width, self.screen_height,
                0, 0, wc.hInstance, None
            )
            
            # Show window (required to receive pointer events)
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
            win32gui.UpdateWindow(self.hwnd)
            
            # Enable pointer messages (disable legacy mouse messages for pointer events)
            if self.EnableMouseInPointer:
                self.EnableMouseInPointer(True)
            
        except Exception as e:
            print(f"Error creating window: {e}")
            import traceback
            traceback.print_exc()
            self.hwnd = None
    
    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """Window procedure to handle pointer messages"""
        try:
            if msg == WM_POINTERDOWN:
                pointer_id = wparam & 0xFFFF
                self._handle_pointer_down(pointer_id)
                return 0
            
            elif msg == WM_POINTERUPDATE:
                pointer_id = wparam & 0xFFFF
                self._handle_pointer_update(pointer_id)
                return 0
            
            elif msg == WM_POINTERUP:
                pointer_id = wparam & 0xFFFF
                self._handle_pointer_up(pointer_id)
                return 0
            
            elif msg == win32con.WM_DESTROY:
                win32gui.PostQuitMessage(0)
                return 0
        
        except Exception as e:
            print(f"Error in window proc: {e}")
        
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
    
    def _handle_pointer_down(self, pointer_id: int):
        """Handle pointer down event"""
        if not self.is_capturing:
            return
        
        pointer_info = POINTER_INFO()
        if self.GetPointerInfo(pointer_id, byref(pointer_info)):
            x = pointer_info.ptPixelLocation.x
            y = pointer_info.ptPixelLocation.y
            
            # Normalize to window coordinates
            window_x, window_y = self._normalize_coords(x, y)
            timestamp = time.monotonic()
            timestamp_ns = time.monotonic_ns()
            
            self.active_touches[pointer_id] = [TouchPoint(window_x, window_y, timestamp, timestamp_ns)]
            
            print(f"👇 Pointer {pointer_id} down at ({window_x:.1f}, {window_y:.1f})")
            
            if self.on_finger_down_callback:
                self.on_finger_down_callback(pointer_id)
    
    def _handle_pointer_update(self, pointer_id: int):
        """Handle pointer update event"""
        if not self.is_capturing or pointer_id not in self.active_touches:
            return
        
        pointer_info = POINTER_INFO()
        if self.GetPointerInfo(pointer_id, byref(pointer_info)):
            x = pointer_info.ptPixelLocation.x
            y = pointer_info.ptPixelLocation.y
            
            # Normalize to window coordinates
            window_x, window_y = self._normalize_coords(x, y)
            timestamp = time.monotonic()
            timestamp_ns = time.monotonic_ns()
            
            self.active_touches[pointer_id].append(TouchPoint(window_x, window_y, timestamp, timestamp_ns))
            
            if self.on_point_added_callback:
                self.on_point_added_callback(pointer_id, window_x, window_y)
    
    def _handle_pointer_up(self, pointer_id: int):
        """Handle pointer up event"""
        if pointer_id not in self.active_touches:
            return
        
        points = self.active_touches[pointer_id]
        self.completed_touches.append(points)
        
        print(f"👆 Pointer {pointer_id} up ({len(points)} points)")
        
        if self.on_finger_up_callback:
            self.on_finger_up_callback(pointer_id, points)
        
        del self.active_touches[pointer_id]
    
    def _message_loop(self):
        """Message loop running in background thread"""
        try:
            while self.running:
                msg = win32gui.GetMessage(None, 0, 0)
                if msg:
                    win32gui.TranslateMessage(msg)
                    win32gui.DispatchMessage(msg)
                else:
                    break
        except Exception as e:
            print(f"Message loop error: {e}")
    
    def _normalize_coords(self, x: int, y: int) -> Tuple[float, float]:
        """Normalize screen coordinates to window coordinates"""
        if self.hwnd:
            # Get window rect
            rect = win32gui.GetWindowRect(self.hwnd)
            window_x = x - rect[0]
            window_y = y - rect[1]
            return (float(window_x), float(window_y))
        else:
            # Fallback to screen normalization
            screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            
            norm_x = x / screen_width if screen_width > 0 else 0.5
            norm_y = y / screen_height if screen_height > 0 else 0.5
            
            window_x = norm_x * self.screen_width
            window_y = norm_y * self.screen_height
            
            return (window_x, window_y)
    
    def start_capture(self):
        """Start capturing gestures"""
        self.is_capturing = True
        self.active_touches.clear()
        self.completed_touches.clear()
        print("🎬 Started capturing pointer events")
    
    def stop_capture(self):
        """Stop capturing gestures"""
        self.is_capturing = False
        print("⏹️ Stopped capturing pointer events")
    
    def clear_gestures(self):
        """Clear all gesture data"""
        self.active_touches.clear()
        self.completed_touches.clear()
    
    def get_all_tracks(self) -> List:
        """Get all tracks (active + completed) - returns list of point lists"""
        all_tracks = []
        
        # Add active touches
        for touch_id, points in self.active_touches.items():
            if points:
                all_tracks.append(points)
        
        # Add completed touches
        all_tracks.extend(self.completed_touches)
        
        return all_tracks
    
    async def process_device_events(self, on_finger_down: Optional[Callable] = None,
                                    on_finger_up: Optional[Callable] = None,
                                    on_point_added: Optional[Callable] = None):
        """
        Process touchpad events asynchronously
        
        Note: Windows pointer events are processed in background thread
        This method just stores callbacks and yields control
        """
        self.on_finger_down_callback = on_finger_down
        self.on_finger_up_callback = on_finger_up
        self.on_point_added_callback = on_point_added
        
        # Keep running and yielding control
        while self.running:
            await asyncio.sleep(0.01)
    
    def close(self):
        """Clean up resources"""
        self.running = False
        if self.hwnd:
            try:
                win32gui.DestroyWindow(self.hwnd)
            except:
                pass
        if self.message_thread and self.message_thread.is_alive():
            self.message_thread.join(timeout=1.0)


def detect_windows_touchpad() -> bool:
    """
    Detect if Windows Precision Touchpad is available
    
    Returns:
        True if touchpad is available, False otherwise
    """
    if not IS_WINDOWS:
        return False
    
    try:
        # Check registry for Precision Touchpad
        import winreg
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\PrecisionTouchPad",
                0,
                winreg.KEY_READ
            )
            winreg.CloseKey(key)
            print(f"✓ Windows Precision Touchpad detected (registry)")
            return True
        except:
            pass
        
        # Check for HID touchpad devices
        import subprocess
        result = subprocess.run(
            ['powershell', '-Command', 
             'Get-PnpDevice -Class Mouse | Where-Object {$_.FriendlyName -like "*touchpad*" -or $_.FriendlyName -like "*touch pad*"} | Select-Object -First 1'],
            capture_output=True,
            text=True
        )
        
        if result.stdout and 'touchpad' in result.stdout.lower():
            print(f"✓ Touchpad device detected")
            return True
        
        return False
    
    except Exception as e:
        print(f"⚠️  Error detecting Windows touchpad: {e}")
        return False


def list_windows_touchpads() -> List[Dict[str, str]]:
    """
    List Windows touchpad devices
    
    Returns:
        List of dicts with device information
    """
    if not IS_WINDOWS:
        return []
    
    devices = []
    
    try:
        if detect_windows_touchpad():
            devices.append({
                'path': 'Windows Pointer Input API',
                'name': 'Windows Precision Touchpad',
                'score': 100,
                'api': 'WM_POINTER'
            })
    except Exception as e:
        print(f"⚠️  Error listing Windows touchpads: {e}")
    
    return devices
