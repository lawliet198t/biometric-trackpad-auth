#!/usr/bin/env python3
"""
Simple Windows Touchpad Reader - Version 2

Uses timeout-based finger-lift detection:
- If a contact ID stops appearing for >50ms, it's considered lifted
- This matches how Linux behaves in practice
"""

import subprocess
import json
import time
from pathlib import Path
from typing import List, Dict, Optional


class SimpleTouchpadReaderV2:
    """
    Touchpad reader with timeout-based lift detection
    """
    
    def __init__(self, exe_path: str = "TouchpadCapture.exe", lift_timeout: float = 0.05):
        self.exe_path = self._find_exe(exe_path)
        self.process = None
        self.running = False
        
        # Contact tracking with timestamps
        self.active_contacts: Dict[int, Dict] = {}  # {contact_id: {X, Y, timestamp, last_seen}}
        self.lift_timeout = lift_timeout  # 50ms default
    
    def _find_exe(self, exe_name: str) -> str:
        """Find the TouchpadCapture executable"""
        possible_paths = [
            exe_name,
            f"TouchpadCapture/bin/{exe_name}",
            f"bin/{exe_name}",
            Path(__file__).parent / exe_name,
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return str(Path(path).absolute())
        
        raise FileNotFoundError(
            f"{exe_name} not found!\n"
            "Build it with: build_rawinput.bat"
        )
    
    def start(self) -> bool:
        """Start reading touchpad data"""
        try:
            print(f"Starting: {self.exe_path}")
            
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
        Read current contact data with timeout-based lift detection
        
        Returns:
            List of active contacts (filters out lifted fingers)
            Empty list [] if all fingers lifted
            None if no data available
        """
        if not self.process or not self.running:
            return None
        
        try:
            line = self.process.stdout.readline()
            if not line:
                return None
            
            line = line.strip()
            if not line:
                return None
            
            try:
                data = json.loads(line)
                
                if data.get('Type') == 'ready':
                    print(f"✓ {data.get('Message')}")
                    return None
                
                elif data.get('Type') == 'contacts':
                    contacts = data.get('Contacts', [])
                    current_time = time.time()
                    
                    # Update last_seen for contacts in this frame
                    seen_ids = set()
                    for contact in contacts:
                        contact_id = contact['ContactId']
                        seen_ids.add(contact_id)
                        
                        self.active_contacts[contact_id] = {
                            'ContactId': contact_id,
                            'X': contact['X'],
                            'Y': contact['Y'],
                            'Timestamp': contact['Timestamp'],
                            'last_seen': current_time
                        }
                    
                    # Remove contacts that haven't been seen recently (lifted)
                    lifted_ids = []
                    for contact_id, contact_data in list(self.active_contacts.items()):
                        if current_time - contact_data['last_seen'] > self.lift_timeout:
                            lifted_ids.append(contact_id)
                    
                    for contact_id in lifted_ids:
                        del self.active_contacts[contact_id]
                    
                    # Return only active contacts
                    active_list = [
                        {
                            'ContactId': c['ContactId'],
                            'X': c['X'],
                            'Y': c['Y'],
                            'Timestamp': c['Timestamp']
                        }
                        for c in self.active_contacts.values()
                    ]
                    
                    return active_list if len(active_list) > 0 else []
                
                elif data.get('Type') == 'error':
                    print(f"✗ Error: {data.get('Message')}")
                    return None
            
            except json.JSONDecodeError:
                print(f"[EXE] {line}")
                return None
        
        except Exception as e:
            print(f"Read error: {e}")
            return None
    
    def get_current_contacts(self) -> Dict[int, Dict]:
        """Get current active contacts"""
        return self.active_contacts.copy()
    
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
    """Demo with timeout-based lift detection"""
    
    reader = SimpleTouchpadReaderV2(lift_timeout=0.05)  # 50ms timeout
    
    if not reader.start():
        return
    
    print("\n" + "="*60)
    print("Touch your touchpad - with lift detection!")
    print("Press Ctrl+C to exit")
    print("="*60 + "\n")
    
    last_contact_count = 0
    last_print_time = time.time()
    print_interval = 0.1
    
    try:
        while True:
            contacts = reader.read_contacts()
            
            if contacts is not None:
                current_time = time.time()
                
                if len(contacts) > 0:
                    if current_time - last_print_time > print_interval:
                        print(f"\r[{time.strftime('%H:%M:%S')}] {len(contacts)} finger(s): ", end="")
                        for contact in contacts:
                            print(f"[{contact['ContactId']}: X={contact['X']}, Y={contact['Y']}] ", end="")
                        print("   ", end="", flush=True)
                        last_print_time = current_time
                    last_contact_count = len(contacts)
                elif last_contact_count > 0:
                    print(f"\r[{time.strftime('%H:%M:%S')}] Fingers lifted (timeout)" + " "*50)
                    last_contact_count = 0
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    finally:
        reader.stop()
        print("✓ Stopped")


if __name__ == "__main__":
    main()
