#!/usr/bin/env python3
"""
Windows Touchpad via UI Automation

Reads contact data from the RawInput.Touchpad UI window.
Since the UI shows the data perfectly, we just read it!
"""

import subprocess
import time
import asyncio
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from pathlib import Path

try:
    import pywinauto
    from pywinauto import Application
    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False
    print("⚠️  pywinauto not installed")
    print("   Install with: pip install pywinauto")


@dataclass
class TouchPoint:
    """Single touch point"""
    x: float
    y: float
    timestamp: float
    timestamp_ns: int


class WindowsTouchpadUIAutomation:
    """
    Read touchpad data from RawInput.Touchpad UI using UI Automation
    """
    
    def __init__(self, exe_path: str = None):
        if not PYWINAUTO_AVAILABLE:
            raise RuntimeError("pywinauto not installed")
        
        self.exe_path = exe_path or self._find_exe()
        self.screen_width = 1200
        self.screen_height = 800
        
        self.active_touches: Dict[int, List[TouchPoint]] = {}
        self.completed_touches: List[List[TouchPoint]] = []
        self.is_capturing = False
        
        self.process = None
        self.app = None
        self.window = None
        
        self.on_finger_down_callback = None
        self.on_finger_up_callback = None
        self.on_point_added_callback = None
        
        self.previous_contacts = {}
    
    def _find_exe(self) -> str:
        """Find RawInput.Touchpad.exe"""
        possible_paths = [
            "RawInput.Touchpad/Source/RawInput.Touchpad/bin/Release/net5.0-windows/RawInput.Touchpad.exe",
            "RawInput.Touchpad.exe",
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return str(Path(path).absolute())
        
        raise FileNotFoundError(
            "RawInput.Touchpad.exe not found!\n"
            "Build it with: build_touchpad.bat"
        )
    
    def open_device(self) -> bool:
        """Start the RawInput.Touchpad app"""
        try:
            print(f"Starting: {self.exe_path}")
            
            # Start the app
            self.app = Application(backend="uia").start(self.exe_path)
            time.sleep(1)
            
            # Connect to the window
            self.window = self.app.window(title_re=".*Touchpad.*")
            
            print("✓ RawInput.Touchpad started")
            print("  Touch your touchpad with multiple fingers!")
            
            return True
            
        except Exception as e:
            print(f"✗ Error starting app: {e}")
            return False
    
    def _read_contacts_from_window(self) -> Dict[int, tuple]:
        """Read contact data from the window text"""
        try:
            # Get window text
            text = self.window.window_text()
            
            # Parse contacts from text
            # Format: "Contact 0: X=500, Y=300"
            contacts = {}
            
            for line in text.split('\n'):
                match = re.search(r'Contact\s+(\d+).*?X[=:]\s*(\d+).*?Y[=:]\s*(\d+)', line, re.IGNORECASE)
                if match:
                    contact_id = int(match.group(1))
                    x = float(match.group(2))
                    y = float(match.group(3))
                    contacts[contact_id] = (x, y)
            
            return contacts
            
        except Exception as e:
            return {}
    
    def _process_contacts(self):
        """Process current contacts"""
        if not self.is_capturing:
            return
        
        try:
            current_contacts = self._read_contacts_from_window()
            timestamp = time.monotonic()
            timestamp_ns = time.monotonic_ns()
            
            # Detect new contacts
            for contact_id, (x, y) in current_contacts.items():
                if contact_id not in self.previous_contacts:
                    # New contact
                    self.active_touches[contact_id] = [
                        TouchPoint(x, y, timestamp, timestamp_ns)
                    ]
                    print(f"👇 Finger {contact_id} down at ({x:.1f}, {y:.1f})")
                    
                    if self.on_finger_down_callback:
                        self.on_finger_down_callback(contact_id)
                else:
                    # Update existing contact
                    prev_x, prev_y = self.previous_contacts[contact_id]
                    if abs(x - prev_x) > 1 or abs(y - prev_y) > 1:  # Movement threshold
                        self.active_touches[contact_id].append(
                            TouchPoint(x, y, timestamp, timestamp_ns)
                        )
                        
                        if self.on_point_added_callback:
                            self.on_point_added_callback(contact_id, x, y)
            
            # Detect lifted contacts
            lifted = set(self.previous_contacts.keys()) - set(current_contacts.keys())
            for contact_id in lifted:
                if contact_id in self.active_touches:
                    points = self.active_touches[contact_id]
                    self.completed_touches.append(points)
                    
                    print(f"👆 Finger {contact_id} up ({len(points)} points)")
                    
                    if self.on_finger_up_callback:
                        self.on_finger_up_callback(contact_id, points)
                    
                    del self.active_touches[contact_id]
            
            self.previous_contacts = current_contacts
            
        except Exception as e:
            pass  # Silently ignore errors
    
    def start_capture(self):
        self.is_capturing = True
        self.active_touches.clear()
        self.completed_touches.clear()
        self.previous_contacts.clear()
        print("🎬 Started capturing")
    
    def stop_capture(self):
        self.is_capturing = False
        print("⏹️ Stopped capturing")
    
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
        
        while True:
            self._process_contacts()
            await asyncio.sleep(0.016)  # ~60 FPS
    
    def close(self):
        if self.app:
            try:
                self.app.kill()
            except:
                pass


# Export
WindowsTouchpadCapture = WindowsTouchpadUIAutomation


def detect_windows_touchpad() -> bool:
    import platform
    if platform.system() != 'Windows':
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
    if not detect_windows_touchpad():
        return []
    
    return [{
        'path': 'UI Automation',
        'name': 'Windows Precision Touchpad (via UI Automation)',
        'score': 90,
        'api': 'UI Automation → RawInput.Touchpad.exe'
    }]
