#!/usr/bin/env python3
"""
Windows Precision Touchpad via Python.NET

Uses emoacht's RawInput.Touchpad C# library via Python.NET (pythonnet).
This provides TRUE multi-touch support on Windows.

Requirements:
    pip install pythonnet
    Download: https://github.com/emoacht/RawInput.Touchpad/releases
"""

import time
import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from pathlib import Path
import sys

# Try to import pythonnet
try:
    import clr
    PYTHONNET_AVAILABLE = True
except ImportError:
    PYTHONNET_AVAILABLE = False
    print("⚠️  pythonnet not installed. Install with: pip install pythonnet")

@dataclass
class TouchPoint:
    """Single touch point with position and timing"""
    x: float
    y: float
    timestamp: float
    timestamp_ns: int


class WindowsTouchpadPythonNET:
    """
    Windows Precision Touchpad using Python.NET bridge to C# library
    
    This provides TRUE multi-touch by using emoacht's proven C# implementation.
    """
    
    def __init__(self, dll_path: str = None):
        if not PYTHONNET_AVAILABLE:
            raise RuntimeError("pythonnet not installed. Run: pip install pythonnet")
        
        self.dll_path = dll_path or self._find_dll()
        self.screen_width = 1200
        self.screen_height = 800
        
        # Touch tracking
        self.active_touches: Dict[int, List[TouchPoint]] = {}
        self.completed_touches: List[List[TouchPoint]] = []
        self.is_capturing = False
        
        # Callbacks
        self.on_finger_down_callback = None
        self.on_finger_up_callback = None
        self.on_point_added_callback = None
        
        # C# objects (will be initialized in open_device)
        self.touchpad_manager = None
        self.form = None
        
        # Track previous contact states
        self.previous_contacts = set()
    
    def _find_dll(self) -> str:
        """Try to find the RawInput.Touchpad DLL"""
        possible_paths = [
            "RawInput.Touchpad.dll",
            "lib/RawInput.Touchpad.dll",
            "bin/RawInput.Touchpad.dll",
            Path(__file__).parent / "RawInput.Touchpad.dll",
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return str(Path(path).absolute())
        
        raise FileNotFoundError(
            "RawInput.Touchpad.dll not found!\n"
            "Download from: https://github.com/emoacht/RawInput.Touchpad/releases\n"
            "Place it in the same directory as this script."
        )
    
    def open_device(self) -> bool:
        """Initialize the C# touchpad library"""
        try:
            print(f"Loading C# library: {self.dll_path}")
            
            # Add reference to the C# DLL
            clr.AddReference(str(self.dll_path))
            
            # Import C# namespaces
            import System
            from System import EventHandler
            from System.Windows.Forms import Application, Form
            
            # Try to import the touchpad classes
            # Note: The actual namespace/class names depend on emoacht's implementation
            # This is a template - adjust based on actual DLL structure
            try:
                # Attempt common namespace patterns
                from RawInput.Touchpad import TouchpadForm
                
                print("✓ C# library loaded successfully")
                
                # Create the form (this handles Raw Input)
                self.form = TouchpadForm()
                
                # Hook into contact events
                # Note: Event names depend on actual implementation
                self.form.ContactsReceived += self._on_contacts_received
                
                print("✓ Windows Precision Touchpad initialized via Python.NET")
                print("  Using emoacht's RawInput.Touchpad library")
                print("")
                print("🎉 TRUE MULTI-TOUCH ENABLED!")
                print("  Touch your touchpad with multiple fingers")
                
                # Show the form
                self.form.Show()
                
                return True
                
            except ImportError as e:
                print(f"⚠️  Could not import touchpad classes: {e}")
                print("   The DLL structure might be different than expected.")
                print("   You may need to adjust the import statements.")
                return False
            
        except Exception as e:
            print(f"✗ Error initializing Python.NET bridge: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _on_contacts_received(self, sender, contacts):
        """
        Handle contact events from C#
        
        This is called when the C# library detects touch contacts.
        The exact signature depends on emoacht's implementation.
        """
        if not self.is_capturing:
            return
        
        try:
            # Convert C# contacts to Python
            current_contacts = set()
            timestamp = time.monotonic()
            timestamp_ns = time.monotonic_ns()
            
            # Process each contact
            for contact in contacts:
                contact_id = contact.ContactId
                x = float(contact.X)
                y = float(contact.Y)
                tip_switch = contact.TipSwitch
                
                current_contacts.add(contact_id)
                
                # Normalize coordinates to window size
                norm_x = (x / 65535.0) * self.screen_width  # Adjust based on actual range
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
        """
        Process touchpad events asynchronously
        
        The C# library handles events in its own thread, so we just need to
        keep the async loop running and process callbacks.
        """
        self.on_finger_down_callback = on_finger_down
        self.on_finger_up_callback = on_finger_up
        self.on_point_added_callback = on_point_added
        
        # Keep the event loop running
        # The C# events will be called from the C# thread
        while True:
            await asyncio.sleep(0.01)
            
            # Process Windows messages if needed
            if self.form:
                try:
                    from System.Windows.Forms import Application
                    Application.DoEvents()
                except:
                    pass
    
    def close(self):
        """Clean up resources"""
        if self.form:
            try:
                self.form.Close()
            except:
                pass
        self.form = None
        self.touchpad_manager = None


# Export as the main class
WindowsTouchpadCapture = WindowsTouchpadPythonNET


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
        'path': 'Python.NET Bridge',
        'name': 'Windows Precision Touchpad (via Python.NET + C#)',
        'score': 100,
        'api': 'Python.NET → C# Raw Input'
    }]
