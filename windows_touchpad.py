#!/usr/bin/env python3
"""
Windows Precision Touchpad Backend

Provides touchpad input capture for Windows using Windows Precision Touchpad API.
Compatible interface with Linux evdev backend.
"""

import platform
import time
import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Tuple

# Check if we're on Windows
IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    try:
        import win32api
        import win32con
        import win32gui
        import threading
        from ctypes import windll, Structure, c_long, byref, POINTER, c_int
        from ctypes.wintypes import DWORD, HANDLE, ULONG, POINT
        
        # Define SM_DIGITIZER constant if not available in win32con
        if not hasattr(win32con, 'SM_DIGITIZER'):
            SM_DIGITIZER = 94
            SM_MAXIMUMTOUCHES = 95
        else:
            SM_DIGITIZER = win32con.SM_DIGITIZER
            SM_MAXIMUMTOUCHES = win32con.SM_MAXIMUMTOUCHES
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
    Windows Precision Touchpad capture using Windows Touch API
    
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
        
        # Window handle for touch messages
        self.hwnd = None
        self.touch_enabled = False
        
        # Message loop thread
        self.message_thread = None
        self.running = False
        
        # Callbacks
        self.on_finger_down_callback = None
        self.on_finger_up_callback = None
        self.on_point_added_callback = None
    
    def open_device(self) -> bool:
        """Initialize Windows touch input with capability checks"""
        try:
            # Check if SDL touch is available
            import pygame
            if not hasattr(pygame, 'FINGERDOWN'):
                print(f"✗ SDL touch events not available in pygame")
                print(f"  Ensure pygame is built with SDL2 touch support")
                return False
            
            # Verify Windows touch capability
            try:
                touch_support = win32api.GetSystemMetrics(SM_DIGITIZER)
                has_touch = (touch_support & 0x40) != 0  # NID_INTEGRATED_TOUCH
                has_multitouch = (touch_support & 0x80) != 0  # NID_MULTI_INPUT
                
                if not (has_touch or has_multitouch):
                    print(f"✗ Windows touch/multitouch not detected")
                    print(f"  This backend requires a Precision Touchpad device")
                    print(f"  Digitizer flags: 0x{touch_support:02X}")
                    return False
                
                max_touches = win32api.GetSystemMetrics(SM_MAXIMUMTOUCHES)
                if max_touches == 0:
                    print(f"✗ No touch points available (SM_MAXIMUMTOUCHES = 0)")
                    print(f"  Precision Touchpad may not be enabled")
                    return False
                
                print(f"✓ Windows Precision Touchpad initialized")
                print(f"  Using Windows Touch API via SDL/pygame")
                print(f"  Max touch points: {max_touches}")
                print(f"  Touch support: {'Yes' if has_touch else 'No'}")
                print(f"  Multitouch: {'Yes' if has_multitouch else 'No'}")
                print(f"")
                print(f"⚠️  IMPORTANT: Ensure pygame window is active to receive touch events")
                print(f"  Touch events are delivered through pygame.FINGERDOWN/MOTION/UP")
                
            except Exception as e:
                print(f"⚠️  Could not verify touch capability: {e}")
                print(f"  Proceeding anyway, but touch may not work")
            
            # Register for touch input
            self.touch_enabled = True
            return True
            
        except ImportError as e:
            print(f"✗ pygame not available: {e}")
            print(f"  Install with: pip install pygame")
            return False
        except Exception as e:
            print(f"✗ Error initializing touch input: {e}")
            return False
    
    def normalize_coords(self, x: int, y: int) -> Tuple[float, float]:
        """Normalize screen coordinates to window coordinates"""
        # Windows gives us screen coordinates, normalize to window size
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
    
    def stop_capture(self):
        """Stop capturing gestures"""
        self.is_capturing = False
    
    def clear_gestures(self):
        """Clear all gesture data"""
        self.active_touches.clear()
        self.completed_touches.clear()
    
    def get_all_tracks(self) -> List:
        """Get all tracks (active + completed) - returns list of point lists"""
        # Convert to compatible format
        all_tracks = []
        
        # Add active touches
        for touch_id, points in self.active_touches.items():
            if points:
                all_tracks.append(points)
        
        # Add completed touches
        all_tracks.extend(self.completed_touches)
        
        return all_tracks
    
    def process_touch_down(self, touch_id: int, x: int, y: int):
        """Handle touch down event"""
        if not self.is_capturing:
            return
        
        window_x, window_y = self.normalize_coords(x, y)
        timestamp = time.monotonic()
        timestamp_ns = time.monotonic_ns()
        
        self.active_touches[touch_id] = [TouchPoint(window_x, window_y, timestamp, timestamp_ns)]
        
        if self.on_finger_down_callback:
            self.on_finger_down_callback(touch_id)
    
    def process_touch_move(self, touch_id: int, x: int, y: int):
        """Handle touch move event"""
        if not self.is_capturing or touch_id not in self.active_touches:
            return
        
        window_x, window_y = self.normalize_coords(x, y)
        timestamp = time.monotonic()
        timestamp_ns = time.monotonic_ns()
        
        self.active_touches[touch_id].append(TouchPoint(window_x, window_y, timestamp, timestamp_ns))
        
        if self.on_point_added_callback:
            self.on_point_added_callback(touch_id, window_x, window_y)
    
    def process_touch_up(self, touch_id: int):
        """Handle touch up event"""
        if touch_id not in self.active_touches:
            return
        
        points = self.active_touches[touch_id]
        self.completed_touches.append(points)
        
        if self.on_finger_up_callback:
            self.on_finger_up_callback(touch_id, points)
        
        del self.active_touches[touch_id]
    
    async def process_device_events(self, on_finger_down: Optional[Callable] = None,
                                    on_finger_up: Optional[Callable] = None,
                                    on_point_added: Optional[Callable] = None):
        """
        Process touchpad events asynchronously
        
        Note: Windows touch events are processed via pygame events
        This method just stores callbacks and yields control
        """
        self.on_finger_down_callback = on_finger_down
        self.on_finger_up_callback = on_finger_up
        self.on_point_added_callback = on_point_added
        
        # Keep running and yielding control
        while True:
            await asyncio.sleep(0.001)


def detect_windows_touchpad() -> bool:
    """
    Detect if Windows Precision Touchpad is available
    
    Returns:
        True if touchpad is available, False otherwise
    """
    if not IS_WINDOWS:
        return False
    
    try:
        # Check if touch is supported
        touch_support = win32api.GetSystemMetrics(SM_DIGITIZER)
        
        # Check for touch support flags
        has_touch = (touch_support & 0x40) != 0  # NID_INTEGRATED_TOUCH
        has_multitouch = (touch_support & 0x80) != 0  # NID_MULTI_INPUT
        
        if has_touch or has_multitouch:
            max_touches = win32api.GetSystemMetrics(SM_MAXIMUMTOUCHES)
            print(f"✓ Windows touch support detected (max touches: {max_touches})")
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
            max_touches = win32api.GetSystemMetrics(SM_MAXIMUMTOUCHES)
            devices.append({
                'path': 'Windows Touch API',
                'name': 'Windows Precision Touchpad',
                'score': 100,
                'max_touches': max_touches
            })
    except Exception as e:
        print(f"⚠️  Error listing Windows touchpads: {e}")
    
    return devices
