#!/usr/bin/env python3
"""
Simple Biometric Capture - Direct Raw Values

Captures raw touchpad data and feeds it directly to biometric feature extraction.
No complex visualization or gesture tracking - just raw X, Y values.
"""

import time
import numpy as np
from simple_windows_touchpad import SimpleTouchpadReader
from typing import List, Dict


class BiometricCapture:
    """
    Minimal biometric capture using raw touchpad values
    """
    
    def __init__(self):
        self.reader = SimpleTouchpadReader()
        self.capturing = False
        
        # Store raw samples for current gesture
        self.current_gesture = []  # List of {time, contacts: [{id, x, y}]}
    
    def start(self) -> bool:
        """Start touchpad reader"""
        return self.reader.start()
    
    def start_capture(self):
        """Start capturing a gesture"""
        self.capturing = True
        self.current_gesture = []
        print("🎬 Capturing gesture...")
    
    def stop_capture(self):
        """Stop capturing and return gesture data"""
        self.capturing = False
        gesture = self.current_gesture.copy()
        self.current_gesture = []
        print(f"⏹️ Captured {len(gesture)} samples")
        return gesture
    
    def update(self):
        """Update - call this in your main loop"""
        contacts = self.reader.read_contacts()
        
        if contacts and self.capturing:
            # Store raw sample
            sample = {
                'time': time.time(),
                'contacts': [
                    {
                        'id': c['ContactId'],
                        'x': c['X'],
                        'y': c['Y']
                    }
                    for c in contacts
                ]
            }
            self.current_gesture.append(sample)
    
    def stop(self):
        """Stop reader"""
        self.reader.stop()


def extract_features(gesture_data: List[Dict]) -> np.ndarray:
    """
    Extract biometric features from raw gesture data
    
    Args:
        gesture_data: List of samples [{time, contacts: [{id, x, y}]}]
    
    Returns:
        Feature vector (numpy array)
    """
    if not gesture_data:
        return np.array([])
    
    features = []
    
    # 1. Number of fingers used
    all_contact_ids = set()
    for sample in gesture_data:
        for contact in sample['contacts']:
            all_contact_ids.add(contact['id'])
    num_fingers = len(all_contact_ids)
    features.append(num_fingers)
    
    # 2. Gesture duration
    if len(gesture_data) > 1:
        duration = gesture_data[-1]['time'] - gesture_data[0]['time']
    else:
        duration = 0
    features.append(duration)
    
    # 3. Average velocity for each finger
    for contact_id in sorted(all_contact_ids):
        # Get all positions for this finger
        positions = []
        times = []
        
        for sample in gesture_data:
            for contact in sample['contacts']:
                if contact['id'] == contact_id:
                    positions.append((contact['x'], contact['y']))
                    times.append(sample['time'])
        
        if len(positions) > 1:
            # Calculate velocity
            total_distance = 0
            for i in range(1, len(positions)):
                dx = positions[i][0] - positions[i-1][0]
                dy = positions[i][1] - positions[i-1][1]
                distance = np.sqrt(dx**2 + dy**2)
                total_distance += distance
            
            total_time = times[-1] - times[0]
            velocity = total_distance / total_time if total_time > 0 else 0
        else:
            velocity = 0
        
        features.append(velocity)
    
    # 4. Pressure variation (if available)
    # For now, just use contact count variation as proxy
    contact_counts = [len(sample['contacts']) for sample in gesture_data]
    if contact_counts:
        features.append(np.mean(contact_counts))
        features.append(np.std(contact_counts))
    
    return np.array(features)


def main():
    """Demo: Capture gestures and extract features"""
    
    capture = BiometricCapture()
    
    if not capture.start():
        print("Failed to start touchpad reader")
        return
    
    print("\n" + "="*60)
    print("Simple Biometric Capture")
    print("="*60)
    print("\nCommands:")
    print("  Press ENTER to start capturing")
    print("  Press ENTER again to stop and extract features")
    print("  Type 'quit' to exit")
    print("="*60 + "\n")
    
    try:
        while True:
            # Update reader
            capture.update()
            
            # Check for user input (non-blocking)
            import select
            import sys
            
            # Simple input handling
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                line = input()
                
                if line.lower() == 'quit':
                    break
                
                if not capture.capturing:
                    capture.start_capture()
                else:
                    gesture_data = capture.stop_capture()
                    
                    if gesture_data:
                        # Extract features
                        features = extract_features(gesture_data)
                        
                        print(f"\n📊 Features extracted:")
                        print(f"   Shape: {features.shape}")
                        print(f"   Values: {features}")
                        print()
            
            time.sleep(0.016)  # 60 FPS
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    finally:
        capture.stop()
        print("✓ Stopped")


if __name__ == "__main__":
    # Windows doesn't have select.select for stdin, so use simpler version
    import platform
    if platform.system() == 'Windows':
        print("Note: On Windows, use Ctrl+C to stop between captures")
        
        capture = BiometricCapture()
        if not capture.start():
            print("Failed to start")
        else:
            print("\nTouch your touchpad for 2 seconds...")
            
            capture.start_capture()
            start_time = time.time()
            
            try:
                while time.time() - start_time < 2.0:
                    capture.update()
                    time.sleep(0.016)
            except KeyboardInterrupt:
                pass
            
            gesture_data = capture.stop_capture()
            
            if gesture_data:
                features = extract_features(gesture_data)
                print(f"\n📊 Features: {features}")
            
            capture.stop()
    else:
        main()
