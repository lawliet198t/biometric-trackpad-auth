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
        """Initialize Windows touchpad capture (via pygame mouse events)"""
        try:
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
            
            if has_precision_touchpad:
                print(f"✓ Windows Precision Touchpad detected")
            else:
                print(f"⚠️  Windows Precision Touchpad not detected in registry")
            
            print(f"✓ Windows touchpad capture initialized")
            print(f"  Using pygame mouse events (touchpad → mouse cursor)")
            print(f"")
            print(f"⚠️  LIMITATION: Windows touchpads only send single cursor position")
            print(f"  • Click and drag with mouse/touchpad to draw gestures")
            print(f"  • True multi-touch requires touchscreen or Linux")
            print(f"  • Each click-drag = one finger gesture")
            
            return True
            
        except Exception as e:
            print(f"✗ Error initializing touchpad capture: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_touch_down(self, touch_id: int, x: float, y: float):
        """Handle touch down event (called from pygame)"""
        if not self.is_capturing:
            return
        
        timestamp = time.monotonic()
        timestamp_ns = time.monotonic_ns()
        
        self.active_touches[touch_id] = [TouchPoint(x, y, timestamp, timestamp_ns)]
        
        if self.on_finger_down_callback:
            self.on_finger_down_callback(touch_id)
    
    def process_touch_move(self, touch_id: int, x: float, y: float):
        """Handle touch move event (called from pygame)"""
        if not self.is_capturing or touch_id not in self.active_touches:
            return
        
        timestamp = time.monotonic()
        timestamp_ns = time.monotonic_ns()
        
        self.active_touches[touch_id].append(TouchPoint(x, y, timestamp, timestamp_ns))
        
        if self.on_point_added_callback:
            self.on_point_added_callback(touch_id, x, y)
    
    def process_touch_up(self, touch_id: int):
        """Handle touch up event (called from pygame)"""
        if touch_id not in self.active_touches:
            return
        
        points = self.active_touches[touch_id]
        self.completed_touches.append(points)
        
        if self.on_finger_up_callback:
            self.on_finger_up_callback(touch_id, points)
        
        del self.active_touches[touch_id]

    
    def start_capture(self):
        """Start capturing gestures"""
        self.is_capturing = True
        self.active_touches.clear()
        self.completed_touches.clear()
        print("🎬 Started capturing (click and drag with mouse/touchpad)")
    
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
