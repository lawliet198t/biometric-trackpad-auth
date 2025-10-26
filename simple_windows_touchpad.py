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
import threading
import queue
from pathlib import Path
from typing import List, Dict, Optional


class SimpleTouchpadReader:
    """
    Minimal touchpad reader - just gets raw X, Y, ContactId values
    Uses threading to avoid blocking
    """
    
    def __init__(self, exe_path: str = "TouchpadCapture.exe"):
        self.exe_path = self._find_exe(exe_path)
        self.process = None
        self.running = False
        
        # Raw contact data
        self.current_contacts: Dict[int, Dict] = {}  # {contact_id: {X, Y, timestamp}}
        
        # Threading for non-blocking reads
        self.data_queue = queue.Queue(maxsize=100)
        self.reader_thread = None
    
    def _find_exe(self, exe_name: str) -> str:
        """Find the TouchpadCapture executable"""
        possible_paths = [
            f"TouchpadCapture/bin/{exe_name}",  # Build output (BEST - has all DLLs)
            exe_name,  # Root directory
            f"TouchpadCapture/bin/Release/net8.0-windows/{exe_name}",
            f"bin/{exe_name}",
            Path(__file__).parent / exe_name,
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                found_path = str(Path(path).absolute())
                print(f"Using: {found_path}")
                return found_path
        
        raise FileNotFoundError(
            f"{exe_name} not found!\n"
            "Build it with: build_rawinput.bat\n"
            f"Searched: {possible_paths}"
        )
    
    def _reader_thread_func(self):
        """Background thread to read from subprocess"""
        while self.running:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break
                
                line = line.strip()
                if line:
                    try:
                        self.data_queue.put(line, block=False)
                    except queue.Full:
                        # Queue full, skip this line
                        pass
            except:
                break
    
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
            
            # Start reader thread
            self.reader_thread = threading.Thread(target=self._reader_thread_func, daemon=True)
            self.reader_thread.start()
            
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
        if not self.running:
            return None
        
        try:
            # Try to get data from queue (non-blocking)
            line = self.data_queue.get(block=False)
            
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
                    
                    # Always return the contacts (even if empty)
                    # Empty array means all fingers lifted
                    return contacts
                
                elif data.get('Type') == 'error':
                    print(f"✗ Error: {data.get('Message')}")
                    return None
            
            except json.JSONDecodeError:
                # Not JSON, just print
                print(f"[EXE] {line}")
                return None
        
        except queue.Empty:
            # No data available right now
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
    last_print_time = time.time()
    print_interval = 0.1  # Print every 100ms for smoother display
    
    try:
        while True:
            contacts = reader.read_contacts()
            
            if contacts is not None:  # Got data
                current_time = time.time()
                
                if len(contacts) > 0:
                    # Active touches - print throttled
                    if current_time - last_print_time > print_interval:
                        print(f"\r[{time.strftime('%H:%M:%S')}] {len(contacts)} finger(s): ", end="")
                        for contact in contacts:
                            print(f"[{contact['ContactId']}: X={contact['X']}, Y={contact['Y']}] ", end="")
                        print("   ", end="", flush=True)
                        last_print_time = current_time
                    last_contact_count = len(contacts)
                elif last_contact_count > 0:
                    # Fingers lifted
                    print(f"\r[{time.strftime('%H:%M:%S')}] Fingers lifted" + " "*50)
                    last_contact_count = 0
            
            time.sleep(0.01)  # 100 FPS polling, but throttled output
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    finally:
        reader.stop()
        print("✓ Stopped")


if __name__ == "__main__":
    main()
