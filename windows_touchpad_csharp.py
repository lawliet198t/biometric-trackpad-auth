#!/usr/bin/env python3
"""
Windows Touchpad via C# Bridge

Uses emoacht's proven C# implementation via subprocess communication.
This is the practical solution that actually works.
"""

import subprocess
import json
import time
import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from pathlib import Path

@dataclass
class TouchPoint:
    x: float
    y: float
    timestamp: float
    timestamp_ns: int

class WindowsTouchpadCSharp:
    """
    Windows Precision Touchpad using C# bridge
    
    This uses a C# executable that handles the Raw Input API properly.
    """
    
    def __init__(self, csharp_exe_path: str = "TouchpadCapture.exe"):
        self.csharp_exe_path = csharp_exe_path
        self.process = None
        
        self.screen_width = 1200
        self.screen_height = 800
        
        self.active_touches: Dict[int, List[TouchPoint]] = {}
        self.completed_touches: List[List[TouchPoint]] = []
        self.is_capturing = False
        
        self.on_finger_down_callback = None
        self.on_finger_up_callback = None
        self.on_point_added_callback = None
    
    def open_device(self) -> bool:
        """Start the C# bridge process"""
        try:
            # Check if C# executable exists
            if not Path(self.csharp_exe_path).exists():
                print(f"✗ C# executable not found: {self.csharp_exe_path}")
                print(f"")
                print(f"To get it:")
                print(f"1. Download from: https://github.com/emoacht/RawInput.Touchpad/releases")
                print(f"2. Or build from source (see BUILD_CSHARP.md)")
                return False
            
            # Start C# process
            self.process = subprocess.Popen(
                [self.csharp_exe_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            print(f"✓ C# Touchpad Bridge started")
            print(f"  Using: {self.csharp_exe_path}")
            print(f"  Process ID: {self.process.pid}")
            print(f"")
            print(f"🎉 TRUE MULTI-TOUCH via C# Bridge!")
            
            return True
            
        except Exception as e:
            print(f"✗ Error starting C# bridge: {e}")
            return False
    
    def start_capture(self):
        """Start capturing"""
        self.is_capturing = True
        self.active_touches.clear()
        self.completed_touches.clear()
        
        if self.process:
            try:
                self.process.stdin.write("START\n")
                self.process.stdin.flush()
            except:
                pass
        
        print("🎬 Started capturing")
    
    def stop_capture(self):
        """Stop capturing"""
        self.is_capturing = False
        
        if self.process:
            try:
                self.process.stdin.write("STOP\n")
                self.process.stdin.flush()
            except:
                pass
        
        print("⏹️ Stopped capturing")
    
    def clear_gestures(self):
        """Clear gestures"""
        self.active_touches.clear()
        self.completed_touches.clear()
    
    def get_all_tracks(self) -> List:
        """Get all tracks"""
        all_tracks = []
        for touch_id, points in self.active_touches.items():
            if points:
                all_tracks.append(points)
        all_tracks.extend(self.completed_touches)
        return all_tracks
    
    async def process_device_events(self, on_finger_down=None, on_finger_up=None, on_point_added=None):
        """Process events from C# bridge"""
        self.on_finger_down_callback = on_finger_down
        self.on_finger_up_callback = on_finger_up
        self.on_point_added_callback = on_point_added
        
        if not self.process:
            return
        
        try:
            while self.process.poll() is None:
                # Read line from C# process
                line = await asyncio.get_event_loop().run_in_executor(
                    None, self.process.stdout.readline
                )
                
                if not line:
                    break
                
                # Parse JSON data from C#
                try:
                    data = json.loads(line.strip())
                    self._process_touch_data(data)
                except json.JSONDecodeError:
                    pass
                
                await asyncio.sleep(0.001)
        
        except Exception as e:
            print(f"Error processing events: {e}")
    
    def _process_touch_data(self, data: dict):
        """Process touch data from C#"""
        if not self.is_capturing:
            return
        
        event_type = data.get('type')
        contact_id = data.get('id')
        x = data.get('x', 0)
        y = data.get('y', 0)
        
        timestamp = time.monotonic()
        timestamp_ns = time.monotonic_ns()
        
        if event_type == 'down':
            self.active_touches[contact_id] = [TouchPoint(x, y, timestamp, timestamp_ns)]
            if self.on_finger_down_callback:
                self.on_finger_down_callback(contact_id)
        
        elif event_type == 'move':
            if contact_id in self.active_touches:
                self.active_touches[contact_id].append(TouchPoint(x, y, timestamp, timestamp_ns))
                if self.on_point_added_callback:
                    self.on_point_added_callback(contact_id, x, y)
        
        elif event_type == 'up':
            if contact_id in self.active_touches:
                points = self.active_touches[contact_id]
                self.completed_touches.append(points)
                if self.on_finger_up_callback:
                    self.on_finger_up_callback(contact_id, points)
                del self.active_touches[contact_id]
    
    def close(self):
        """Cleanup"""
        if self.process:
            try:
                self.process.stdin.write("QUIT\n")
                self.process.stdin.flush()
                self.process.wait(timeout=2)
            except:
                self.process.kill()
            self.process = None


# Export
WindowsTouchpadCapture = WindowsTouchpadCSharp

def detect_windows_touchpad() -> bool:
    """Detect touchpad"""
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
    """List touchpads"""
    if not detect_windows_touchpad():
        return []
    
    return [{
        'path': 'C# Bridge',
        'name': 'Windows Precision Touchpad (via C#)',
        'score': 100,
        'api': 'C# Raw Input'
    }]
