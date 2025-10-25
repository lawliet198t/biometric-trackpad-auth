#!/usr/bin/env python3
"""
Windows Precision Touchpad Backend

Provides touchpad input capture for Windows using Raw Input API.
Compatible interface with Linux evdev backend.
"""

import platform
import time
import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Tuple
from ctypes import (windll, Structure, POINTER, c_int, c_uint, byref, c_void_p, 
                    sizeof, cast, c_ubyte, c_ushort, c_long)
from ctypes.wintypes import DWORD, HWND, UINT, WPARAM, LPARAM, HANDLE, WORD

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

# Raw Input API Constants
WM_INPUT = 0x00FF
RIDEV_INPUTSINK = 0x00000100
RID_INPUT = 0x10000003

RIM_TYPEMOUSE = 0
RIM_TYPEKEYBOARD = 1
RIM_TYPEHID = 2

# HID Usage Pages
HID_USAGE_PAGE_GENERIC = 0x01
HID_USAGE_PAGE_DIGITIZER = 0x0D

# HID Usages
HID_USAGE_GENERIC_MOUSE = 0x02
HID_USAGE_DIGITIZER_TOUCH_PAD = 0x05

# Raw Input structures
class RAWINPUTDEVICE(Structure):
    _fields_ = [
        ("usUsagePage", c_ushort),
        ("usUsage", c_ushort),
        ("dwFlags", DWORD),
        ("hwndTarget", HWND),
    ]

class RAWINPUTHEADER(Structure):
    _fields_ = [
        ("dwType", DWORD),
        ("dwSize", DWORD),
        ("hDevice", HANDLE),
        ("wParam", WPARAM),
    ]

class RAWMOUSE(Structure):
    _fields_ = [
        ("usFlags", c_ushort),
        ("usButtonFlags", c_ushort),
        ("usButtonData", c_ushort),
        ("ulRawButtons", c_uint),
        ("lLastX", c_long),
        ("lLastY", c_long),
        ("ulExtraInformation", c_uint),
    ]

class RAWHID(Structure):
    _fields_ = [
        ("dwSizeHid", DWORD),
        ("dwCount", DWORD),
        ("bRawData", c_ubyte * 1),
    ]

class RAWINPUT_UNION(Structure):
    _fields_ = [
        ("mouse", RAWMOUSE),
        ("hid", RAWHID),
    ]

class RAWINPUT(Structure):
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("data", RAWINPUT_UNION),
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
    Windows Precision Touchpad capture using Raw Input API
    
    Compatible interface with Linux TrackpadCapture
    """
    
    def __init__(self):
        if not IS_WINDOWS:
            raise RuntimeError("WindowsTouchpadCapture only works on Windows")
        
        self.screen_width = 1200
        self.screen_height = 800
        
        # Touch tracking (simulated from mouse movements)
        self.active_touches: Dict[int, List[TouchPoint]] = {}
        self.completed_touches: List[List[TouchPoint]] = []
        self.is_capturing = False
        
        # Mouse tracking for touchpad simulation
        self.last_mouse_pos = None
        self.mouse_down = False
        self.current_track_id = 0
        
        # Window handle
        self.hwnd = None
        
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
            
            # RegisterRawInputDevices
            self.RegisterRawInputDevices = self.user32.RegisterRawInputDevices
            self.RegisterRawInputDevices.argtypes = [POINTER(RAWINPUTDEVICE), UINT, UINT]
            self.RegisterRawInputDevices.restype = c_int
            
            # GetRawInputData
            self.GetRawInputData = self.user32.GetRawInputData
            self.GetRawInputData.argtypes = [HANDLE, UINT, c_void_p, POINTER(UINT), UINT]
            self.GetRawInputData.restype = c_int
            
        except Exception as e:
            print(f"⚠️  Error loading Raw Input API: {e}")
            self.user32 = None
    
    def open_device(self) -> bool:
        """Initialize Windows Raw Input with capability checks"""
        try:
            if self.user32 is None:
                print(f"✗ Windows Raw Input API not available")
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
                print(f"  Will capture mouse events as touchpad simulation")
            else:
                print(f"✓ Windows Precision Touchpad detected")
            
            # Create window for receiving raw input
            self._create_message_window()
            
            if self.hwnd is None:
                print(f"✗ Failed to create message window")
                return False
            
            # Register for raw input from mouse/touchpad
            devices = (RAWINPUTDEVICE * 1)()
            
            # Register for mouse input (touchpad sends mouse events)
            devices[0].usUsagePage = HID_USAGE_PAGE_GENERIC
            devices[0].usUsage = HID_USAGE_GENERIC_MOUSE
            devices[0].dwFlags = RIDEV_INPUTSINK
            devices[0].hwndTarget = self.hwnd
            
            if not self.RegisterRawInputDevices(devices, 1, sizeof(RAWINPUTDEVICE)):
                print(f"✗ Failed to register raw input devices")
                return False
            
            print(f"✓ Windows Raw Input initialized")
            print(f"  Capturing mouse/touchpad events")
            print(f"  Window handle: 0x{self.hwnd:08X}")
            print(f"")
            print(f"⚠️  IMPORTANT: Click and drag in the window to simulate touch")
            print(f"  Note: True multi-touch requires touchscreen, not touchpad")
            
            # Start message loop in background thread
            self.running = True
            self.message_thread = threading.Thread(target=self._message_loop, daemon=True)
            self.message_thread.start()
            
            return True
            
        except Exception as e:
            print(f"✗ Error initializing Raw Input: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_message_window(self):
        """Create a window to receive raw input messages"""
        try:
            # Register window class
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self._wnd_proc
            wc.lpszClassName = "TouchpadCaptureWindow"
            wc.hInstance = win32api.GetModuleHandle(None)
            wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
            wc.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)
            
            try:
                class_atom = win32gui.RegisterClass(wc)
            except Exception:
                pass
            
            # Create window
            self.hwnd = win32gui.CreateWindow(
                "TouchpadCaptureWindow",
                "Touchpad Capture - Click and drag to test",
                win32con.WS_OVERLAPPEDWINDOW | win32con.WS_VISIBLE,
                100, 100, self.screen_width, self.screen_height,
                0, 0, wc.hInstance, None
            )
            
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
            win32gui.UpdateWindow(self.hwnd)
            
        except Exception as e:
            print(f"Error creating window: {e}")
            import traceback
            traceback.print_exc()
            self.hwnd = None
    
    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """Window procedure to handle messages"""
        try:
            if msg == WM_INPUT:
                self._handle_raw_input(lparam)
                return 0
            
            elif msg == win32con.WM_LBUTTONDOWN:
                # Mouse button down - start tracking
                x = win32api.LOWORD(lparam)
                y = win32api.HIWORD(lparam)
                self._handle_mouse_down(x, y)
                return 0
            
            elif msg == win32con.WM_MOUSEMOVE:
                # Mouse move - add points
                x = win32api.LOWORD(lparam)
                y = win32api.HIWORD(lparam)
                if wparam & win32con.MK_LBUTTON:
                    self._handle_mouse_move(x, y)
                return 0
            
            elif msg == win32con.WM_LBUTTONUP:
                # Mouse button up - end tracking
                self._handle_mouse_up()
                return 0
            
            elif msg == win32con.WM_DESTROY:
                win32gui.PostQuitMessage(0)
                return 0
        
        except Exception as e:
            print(f"Error in window proc: {e}")
        
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
    
    def _handle_raw_input(self, lparam):
        """Handle WM_INPUT message"""
        try:
            # Get size of raw input data
            size = UINT(0)
            self.GetRawInputData(lparam, RID_INPUT, None, byref(size), sizeof(RAWINPUTHEADER))
            
            if size.value == 0:
                return
            
            # Allocate buffer and get data
            buffer = (c_ubyte * size.value)()
            result = self.GetRawInputData(lparam, RID_INPUT, buffer, byref(size), sizeof(RAWINPUTHEADER))
            
            if result != size.value:
                return
            
            # Parse RAWINPUT structure
            raw = cast(buffer, POINTER(RAWINPUT)).contents
            
            # We're mainly interested in mouse movements from touchpad
            if raw.header.dwType == RIM_TYPEMOUSE:
                mouse = raw.data.mouse
                # Raw mouse data available here if needed
                pass
            
        except Exception as e:
            pass  # Silently ignore parsing errors
    
    def _handle_mouse_down(self, x: int, y: int):
        """Handle mouse button down (simulates finger down)"""
        if not self.is_capturing:
            return
        
        self.mouse_down = True
        self.current_track_id += 1
        
        timestamp = time.monotonic()
        timestamp_ns = time.monotonic_ns()
        
        self.active_touches[self.current_track_id] = [
            TouchPoint(float(x), float(y), timestamp, timestamp_ns)
        ]
        self.last_mouse_pos = (x, y)
        
        print(f"👇 Touch {self.current_track_id} down at ({x}, {y})")
        
        if self.on_finger_down_callback:
            self.on_finger_down_callback(self.current_track_id)
    
    def _handle_mouse_move(self, x: int, y: int):
        """Handle mouse move (simulates finger move)"""
        if not self.is_capturing or not self.mouse_down:
            return
        
        if self.current_track_id not in self.active_touches:
            return
        
        timestamp = time.monotonic()
        timestamp_ns = time.monotonic_ns()
        
        self.active_touches[self.current_track_id].append(
            TouchPoint(float(x), float(y), timestamp, timestamp_ns)
        )
        self.last_mouse_pos = (x, y)
        
        if self.on_point_added_callback:
            self.on_point_added_callback(self.current_track_id, float(x), float(y))
    
    def _handle_mouse_up(self):
        """Handle mouse button up (simulates finger up)"""
        if not self.mouse_down:
            return
        
        self.mouse_down = False
        
        if self.current_track_id in self.active_touches:
            points = self.active_touches[self.current_track_id]
            self.completed_touches.append(points)
            
            print(f"👆 Touch {self.current_track_id} up ({len(points)} points)")
            
            if self.on_finger_up_callback:
                self.on_finger_up_callback(self.current_track_id, points)
            
            del self.active_touches[self.current_track_id]
    
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
    
    def start_capture(self):
        """Start capturing gestures"""
        self.is_capturing = True
        self.active_touches.clear()
        self.completed_touches.clear()
        self.current_track_id = 0
        print("🎬 Started capturing (click and drag in window)")
    
    def stop_capture(self):
        """Stop capturing gestures"""
        self.is_capturing = False
        print("⏹️ Stopped capturing")
    
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
        
        Note: Windows events are processed in background thread
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
            text=True,
            timeout=5
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
                'path': 'Windows Raw Input API',
                'name': 'Windows Precision Touchpad (Mouse Events)',
                'score': 100,
                'api': 'Raw Input + Mouse'
            })
    except Exception as e:
        print(f"⚠️  Error listing Windows touchpads: {e}")
    
    return devices
