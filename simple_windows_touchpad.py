#!/usr/bin/env python3
"""
Simple Windows Touchpad - Direct Raw Values

Directly reads raw touchpad contact data from RawInput.Touchpad.dll
via a minimal C# subprocess. No complex abstractions.

Usage:
    python simple_windows_touchpad.py
"""

import subprocess
import json
import time
from pathlib import Path
from typing import List, Dict, Optional


class SimpleTouchpadReader:
    """
    Minimal touchpad reader - just gets raw X, Y, ContactId values
    """
    
    def __init__(self, exe_path: str = "TouchpadCapture.exe"):
        self.exe_path = self._find_exe(exe_path)
        self.process = None
        self.running = False
        
        # Raw contact data
        self.current_contacts: Dict[int, Dict] = {}  # {contact_id: {X, Y, timestamp}}
    
    def _find_exe(self, exe_name: str) -> str:
        """Find the TouchpadCapture executable"""
        possible_paths = [
            exe_name,
            f"TouchpadCapture/bin/Release/net5.0-windows/{exe_name}",
            f"bin/{exe_name}",
            Path(__file__).parent / exe_name,
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return str(Path(path).absolute())
        
        raise FileNotFoundError(
            f"{exe_name} not found!\n"
            "Build it with: build_touchpad.bat"
        )
    
    def start(self) -> bool:
        """Start reading touchpad data"""
        try:
            print(f"Starting: {self.exe_path}")
            
            # Start subprocess
            self.process = subprocess.Popen(
                [self.exe_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            self.running = True
            print("✓ Touchpad reader started")
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def read_contacts(self) -> Optional[List[Dict]]:
        """
        Read current contact data (non-blocking)
        
        Returns:
            List of contacts: [{ContactId, X, Y, Timestamp}, ...]
            None if no data available
            Empty list [] if no contacts (fingers lifted)
        """
        if not self.process or not self.running:
            return None
        
        try:
            # Non-blocking read
            line = self.process.stdout.readline()
            if not line:
                return None
            
            line = line.strip()
            if not line:
                return None
            
            # Parse JSON
            try:
                data = json.loads(line)
                
                if data.get('Type') == 'ready':
                    print(f"✓ {data.get('Message')}")
                    return None
                
                elif data.get('Type') == 'contacts':
                    contacts = data.get('Contacts', [])
                    
                    # Update current contacts
                    self.current_contacts.clear()
                    
                    if len(contacts) > 0:
                        # Active touches
                        for contact in contacts:
                            contact_id = contact['ContactId']
                            self.current_contacts[contact_id] = {
                                'X': contact['X'],
                                'Y': contact['Y'],
                                'Timestamp': contact['Timestamp']
                            }
                        return contacts
                    else:
                        # No touches - fingers lifted
                        return []
                
                elif data.get('Type') == 'error':
                    print(f"✗ Error: {data.get('Message')}")
                    return None
            
            except json.JSONDecodeError:
                # Not JSON, just print
                print(f"[EXE] {line}")
                return None
        
        except Exception as e:
            print(f"Read error: {e}")
            return None
    
    def get_current_contacts(self) -> Dict[int, Dict]:
        """
        Get current active contacts
        
        Returns:
            {contact_id: {X, Y, Timestamp}, ...}
        """
        return self.current_contacts.copy()
    
    def stop(self):
        """Stop reading"""
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                self.process.kill()
        self.process = None


def main():
    """Simple demo - print raw touchpad values"""
    
    reader = SimpleTouchpadReader()
    
    if not reader.start():
        return
    
    print("\n" + "="*60)
    print("Touch your touchpad - raw values will appear below")
    print("Press Ctrl+C to exit")
    print("="*60 + "\n")
    
    last_contact_count = 0
    
    try:
        while True:
            contacts = reader.read_contacts()
            
            if contacts is not None:  # Got data
                if len(contacts) > 0:
                    # Active touches - print in real-time
                    print(f"\r[{time.strftime('%H:%M:%S')}] {len(contacts)} finger(s): ", end="")
                    for contact in contacts:
                        print(f"[{contact['ContactId']}: X={contact['X']}, Y={contact['Y']}] ", end="")
                    print("   ", end="", flush=True)
                    last_contact_count = len(contacts)
                elif last_contact_count > 0:
                    # Fingers lifted
                    print(f"\r[{time.strftime('%H:%M:%S')}] Fingers lifted" + " "*50)
                    last_contact_count = 0
            
            time.sleep(0.016)  # ~60 FPS
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    finally:
        reader.stop()
        print("✓ Stopped")


if __name__ == "__main__":
    main()
