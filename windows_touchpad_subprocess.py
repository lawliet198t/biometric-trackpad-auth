#!/usr/bin/env python3
"""
Windows Precision Touchpad via C# Subprocess

Uses TouchpadCapture.exe (C# console app) via subprocess communication.
TRUE multi-touch support with zero Python.NET complexity!

Requirements:
    - TouchpadCapture.exe (build with: build_touchpad.bat)
    - No Python.NET needed!
"""

import subprocess
import json
import time
import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from pathlib import Path
import threading
import queue


@dataclass
class TouchPoint:
    """Single touch point with position and timing"""
    x: float
    y: float
    timestamp: float
    timestamp_ns: int


class WindowsTouchpadSubprocess:
    """
    Windows Precision Touchpad using subprocess communication
    
    This is simpler and more reliable than Python.NET!
    """
    
    def __init__(self, exe_path: str = None):
        self.exe_path = exe_path or self._find_exe()
        self.screen_width = 1200
        self.screen_height = 800
        self.ready = False
        
        # Touch tracking
        self.active_touches: Dict[int, List[TouchPoint]] = {}
        self.completed_touches: List[List[TouchPoint]] = []
        self.is_capturing = False
        
        # Callbacks
        self.on_finger_down_callback = None
        self.on_finger_up_callback = None
        self.on_point_added_callback = None
        
        # Subprocess
        self.process = None
        self.output_queue = queue.Queue()
        self.reader_thread = None
        
        # Track previous contact states
        self.previous_contacts = set()
    
    def _find_exe(self) -> str:
        """Try to find the TouchpadCapture EXE"""
        possible_paths = [
            "TouchpadCapture.exe",
            "TouchpadCapture/bin/Release/net5.0-windows/TouchpadCapture.exe",
            "bin/TouchpadCapture.exe",
            Path(__file__).parent / "TouchpadCapture.exe",
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return str(Path(path).absolute())
        
        raise FileNotFoundError(
            "TouchpadCapture.exe not found!\n"
            "Build it with: build_touchpad.bat"
        )
    
    def _read_output(self):
        """Read output from subprocess in a separate thread"""
        try:
            for line in iter(self.process.stdout.readline, ''):
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Try to parse as JSON
                try:
                    data = json.loads(line)
                    self.output_queue.put(data)
                except json.JSONDecodeError:
                    # Not JSON, just print it
                    print(f"[EXE] {line}")
        except Exception as e:
            print(f"Error reading subprocess output: {e}")
    
    def open_device(self) -> bool:
        """Start the subprocess"""
        try:
            print(f"Starting subprocess: {self.exe_path}")
            
            # Start the EXE
            self.process = subprocess.Popen(
                [self.exe_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Start reader thread
            self.reader_thread = threading.Thread(
                target=self._read_output,
                daemon=True
            )
            self.reader_thread.start()
            
            print("✓ Subprocess started")
            print("  Waiting for touchpad events...")
            
            return True
            
        except Exception as e:
            print(f"✗ Error starting subprocess: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _process_contacts(self, contacts_data):
        """Process contact data from subprocess"""
        if not self.is_capturing:
            return
        
        try:
            current_contacts = set()
            timestamp = time.monotonic()
            timestamp_ns = time.monotonic_ns()
            
            # Process each contact
            for contact in contacts_data:
                contact_id = contact['ContactId']
                x = float(contact['X'])
                y = float(contact['Y'])
                tip_switch = contact['TipSwitch']
                
                current_contacts.add(contact_id)
                
                # Normalize coordinates
                norm_x = (x / 65535.0) * self.screen_width
                norm_y = (y / 65535.0) * self.screen_height
                
                if tip_switch:
                    # Contact is active
                    if contact_id not in self.active_touches:
                        # New contact
                        self.active_touches[contact_id] = [
                            TouchPoint(norm_x, norm_y, timestamp, timestamp_ns)
                        ]
                        print(f"👇 Finger {contact_id} down at ({norm_x:.1f}, {norm_y:.1f})")
                        
                        if self.on_finger_down_callback:
                            self.on_finger_down_callback(contact_id)
                    else:
                        # Update existing contact
                        self.active_touches[contact_id].append(
                            TouchPoint(norm_x, norm_y, timestamp, timestamp_ns)
                        )
                        
                        if self.on_point_added_callback:
                            self.on_point_added_callback(contact_id, norm_x, norm_y)
            
            # Detect lifted contacts
            lifted = self.previous_contacts - current_contacts
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
            print(f"Error processing contacts: {e}")
    
    def start_capture(self):
        """Start capturing gestures"""
        self.is_capturing = True
        self.active_touches.clear()
        self.completed_touches.clear()
        self.previous_contacts.clear()
        print("🎬 Started capturing multi-touch gestures")
    
    def stop_capture(self):
        """Stop capturing gestures"""
        self.is_capturing = False
        print("⏹️ Stopped capturing")
    
    def clear_gestures(self):
        """Clear all gesture data"""
        self.active_touches.clear()
        self.completed_touches.clear()
    
    def get_all_tracks(self) -> List:
        """Get all tracks (active + completed)"""
        all_tracks = []
        
        for touch_id, points in self.active_touches.items():
            if points:
                all_tracks.append(points)
        
        all_tracks.extend(self.completed_touches)
        
        return all_tracks
    
    async def process_device_events(self, on_finger_down=None, on_finger_up=None, on_point_added=None):
        """Process touchpad events asynchronously"""
        self.on_finger_down_callback = on_finger_down
        self.on_finger_up_callback = on_finger_up
        self.on_point_added_callback = on_point_added
        
        # Process events from queue
        while True:
            try:
                # Check for data with timeout
                try:
                    data = self.output_queue.get(timeout=0.01)
                    
                    # Process the data
                    if isinstance(data, dict):
                        if data.get('Type') == 'ready':
                            self.ready = True
                            print(f"✓ {data.get('Message')}")
                        elif data.get('Type') == 'contacts':
                            self._process_contacts(data.get('Contacts', []))
                        elif data.get('Type') == 'error':
                            print(f"✗ Error from C# app: {data.get('Message')}")
                    
                except queue.Empty:
                    pass
                
                await asyncio.sleep(0.01)
                
            except Exception as e:
                print(f"Error in event loop: {e}")
                await asyncio.sleep(0.1)
    
    def close(self):
        """Clean up resources"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                self.process.kill()
        self.process = None


# Export as the main class
WindowsTouchpadCapture = WindowsTouchpadSubprocess


def detect_windows_touchpad() -> bool:
    """Detect if Windows Precision Touchpad is available"""
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
    """List Windows touchpad devices"""
    if not detect_windows_touchpad():
        return []
    
    return [{
        'path': 'Subprocess',
        'name': 'Windows Precision Touchpad (via subprocess)',
        'score': 100,
        'api': 'Subprocess → C# EXE'
    }]
