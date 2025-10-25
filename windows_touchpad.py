#!/usr/bin/env python3
"""
Windows Precision Touchpad Backend

For true multi-touch on Windows, use the C# bridge solution.
See README_WINDOWS_TOUCHPAD.md for details.

This file provides a fallback mouse simulation for basic testing.
"""

import platform
import time
import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Tuple

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


@dataclass
class TouchPoint:
    """Single touch point with position and timing"""
    x: float
    y: float
    timestamp: float
    timestamp_ns: int


class WindowsTouchpadCapture:
    """
    Windows touchpad capture (mouse simulation fallback)
    
    NOTE: This only supports single-point (mouse) input.
    For TRUE multi-touch, use the C# bridge solution:
    See README_WINDOWS_TOUCHPAD.md
    """
    
    def __init__(self):
        if not IS_WINDOWS:
            raise RuntimeError("WindowsTouchpadCapture only works on Windows")
        
        self.screen_width = 1200
        self.screen_height = 800
        
        self.active_touches: Dict[int, List[TouchPoint]] = {}
        self.completed_touches: List[List[TouchPoint]] = []
        self.is_capturing = False
        
        self.mouse_down = False
        self.current_track_id = 0
        
        self.hwnd = None
        self.running = False
        self.message_thread = None
        
        self.on_finger_down_callback = None
        self.on_finger_up_callback = None
        self.on_point_added_callback = None
    
    def open_device(self) -> bool:
        """Initialize mouse capture (fallback mode)"""
        try:
            print("⚠️  WARNING: Using mouse simulation (single-point only)")
            print("   For TRUE multi-touch, use C# bridge solution")
            print("   See: README_WINDOWS_TOUCHPAD.md")
            print("")
            
            self._create_window()
            
            if self.hwnd is None:
                return False
            
            self.running = True
            self.message_thread = threading.Thread(target=self._message_loop, daemon=True)
            self.message_thread.start()
            
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def _create_window(self):
        """Create window for mouse input"""
        try:
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self._wnd_proc
            wc.lpszClassName = "TouchpadWindow"
            wc.hInstance = win32api.GetModuleHandle(None)
            
            try:
                win32gui.RegisterClass(wc)
            except:
                pass
            
            self.hwnd = win32gui.CreateWindow(
                "TouchpadWindow",
                "Touchpad Capture (Mouse Mode) - Click and drag",
                win32con.WS_OVERLAPPEDWINDOW | win32con.WS_VISIBLE,
                100, 100, self.screen_width, self.screen_height,
                0, 0, wc.hInstance, None
            )
            
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
            win32gui.UpdateWindow(self.hwnd)
            
        except Exception as e:
            print(f"Error creating window: {e}")
            self.hwnd = None
    
    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """Window procedure"""
        try:
            if msg == win32con.WM_LBUTTONDOWN:
                x = win32api.LOWORD(lparam)
                y = win32api.HIWORD(lparam)
                self._handle_mouse_down(x, y)
                return 0
            
            elif msg == win32con.WM_MOUSEMOVE:
                if wparam & win32con.MK_LBUTTON:
                    x = win32api.LOWORD(lparam)
                    y = win32api.HIWORD(lparam)
                    self._handle_mouse_move(x, y)
                return 0
            
            elif msg == win32con.WM_LBUTTONUP:
                self._handle_mouse_up()
                return 0
            
            elif msg == win32con.WM_DESTROY:
                win32gui.PostQuitMessage(0)
                return 0
        
        except Exception as e:
            print(f"Error in wnd_proc: {e}")
        
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
    
    def _handle_mouse_down(self, x: int, y: int):
        """Handle mouse down"""
        if not self.is_capturing:
            return
        
        self.mouse_down = True
        self.current_track_id += 1
        
        timestamp = time.monotonic()
        timestamp_ns = time.monotonic_ns()
        
        self.active_touches[self.current_track_id] = [
            TouchPoint(float(x), float(y), timestamp, timestamp_ns)
        ]
        
        if self.on_finger_down_callback:
            self.on_finger_down_callback(self.current_track_id)
    
    def _handle_mouse_move(self, x: int, y: int):
        """Handle mouse move"""
        if not self.is_capturing or not self.mouse_down:
            return
        
        if self.current_track_id not in self.active_touches:
            return
        
        timestamp = time.monotonic()
        timestamp_ns = time.monotonic_ns()
        
        self.active_touches[self.current_track_id].append(
            TouchPoint(float(x), float(y), timestamp, timestamp_ns)
        )
        
        if self.on_point_added_callback:
            self.on_point_added_callback(self.current_track_id, float(x), float(y))
    
    def _handle_mouse_up(self):
        """Handle mouse up"""
        if not self.mouse_down:
            return
        
        self.mouse_down = False
        
        if self.current_track_id in self.active_touches:
            points = self.active_touches[self.current_track_id]
            self.completed_touches.append(points)
            
            if self.on_finger_up_callback:
                self.on_finger_up_callback(self.current_track_id, points)
            
            del self.active_touches[self.current_track_id]
    
    def _message_loop(self):
        """Message loop"""
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
        self.is_capturing = True
        self.active_touches.clear()
        self.completed_touches.clear()
        self.current_track_id = 0
    
    def stop_capture(self):
        self.is_capturing = False
    
    def clear_gestures(self):
        self.active_touches.clear()
        self.completed_touches.clear()
    
    def get_all_tracks(self) -> List:
        all_tracks = []
        for touch_id, points in self.active_touches.items():
            if points:
                all_tracks.append(points)
        all_tracks.extend(self.completed_touches)
        return all_tracks
    
    async def process_device_events(self, on_finger_down=None, on_finger_up=None, on_point_added=None):
        self.on_finger_down_callback = on_finger_down
        self.on_finger_up_callback = on_finger_up
        self.on_point_added_callback = on_point_added
        
        while self.running:
            await asyncio.sleep(0.01)
    
    def close(self):
        self.running = False
        if self.hwnd:
            try:
                win32gui.DestroyWindow(self.hwnd)
            except:
                pass


def detect_windows_touchpad() -> bool:
    """Detect if Windows Precision Touchpad is available"""
    if not IS_WINDOWS:
        return False
    
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\PrecisionTouchPad",
            0,
            winreg.KEY_READ
        )
        winreg.CloseKey(key)
        return True
    except:
        return False


def list_windows_touchpads() -> List[Dict[str, str]]:
    """List Windows touchpad devices"""
    if not IS_WINDOWS:
        return []
    
    devices = []
    
    try:
        if detect_windows_touchpad():
            devices.append({
                'path': 'Mouse Simulation',
                'name': 'Windows Precision Touchpad (Mouse Mode - Single Point)',
                'score': 50,
                'note': 'For multi-touch, use C# bridge (see README_WINDOWS_TOUCHPAD.md)'
            })
    except Exception as e:
        print(f"⚠️  Error listing Windows touchpads: {e}")
    
    return devices
