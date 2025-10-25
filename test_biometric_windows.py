#!/usr/bin/env python3
"""
Test Windows Touchpad with Biometric Capture

Simple test to verify the Windows touchpad integration works
with biometric feature extraction.
"""

import time
import numpy as np
from simple_windows_touchpad import SimpleTouchpadReader

def extract_simple_features(gesture_samples):
    """
    Extract simple biometric features from gesture samples
    
    Args:
        gesture_samples: List of {time, contacts: [{id, x, y}]}
    
    Returns:
        Feature dict
    """
    if not gesture_samples:
        return None
    
    features = {}
    
    # 1. Duration
    if len(gesture_samples) > 1:
        duration = gesture_samples[-1]['time'] - gesture_samples[0]['time']
        features['duration'] = duration
    else:
        features['duration'] = 0
    
    # 2. Number of fingers used
    all_contact_ids = set()
    for sample in gesture_samples:
        for contact in sample['contacts']:
            all_contact_ids.add(contact['id'])
    features['num_fingers'] = len(all_contact_ids)
    
    # 3. For each finger, calculate velocity
    velocities = []
    for contact_id in sorted(all_contact_ids):
        # Get all positions for this finger
        positions = []
        times = []
        
        for sample in gesture_samples:
            for contact in sample['contacts']:
                if contact['id'] == contact_id:
                    positions.append((contact['x'], contact['y']))
                    times.append(sample['time'])
        
        if len(positions) > 1:
            # Calculate average velocity
            total_distance = 0
            for i in range(1, len(positions)):
                dx = positions[i][0] - positions[i-1][0]
                dy = positions[i][1] - positions[i-1][1]
                distance = np.sqrt(dx**2 + dy**2)
                total_distance += distance
            
            total_time = times[-1] - times[0]
            velocity = total_distance / total_time if total_time > 0 else 0
            velocities.append(velocity)
    
    if velocities:
        features['avg_velocity'] = np.mean(velocities)
        features['max_velocity'] = np.max(velocities)
    else:
        features['avg_velocity'] = 0
        features['max_velocity'] = 0
    
    return features


def main():
    """Test Windows touchpad with biometric capture"""
    
    print("="*60)
    print("Windows Touchpad Biometric Test")
    print("="*60)
    print()
    print("This will:")
    print("  1. Start the touchpad reader")
    print("  2. Capture a gesture (2 seconds)")
    print("  3. Extract biometric features")
    print()
    print("Make sure the TouchpadCapture window stays open!")
    print()
    
    # Start reader
    reader = SimpleTouchpadReader()
    
    if not reader.start():
        print("✗ Failed to start touchpad reader")
        return
    
    print("✓ Touchpad reader started")
    print()
    
    # Wait for ready message
    time.sleep(1)
    
    # Capture gesture
    print("Touch your touchpad NOW for 2 seconds...")
    print("(Use 2-3 fingers and move them around)")
    print()
    
    gesture_samples = []
    start_time = time.time()
    capture_duration = 2.0
    
    last_print_time = start_time
    
    while time.time() - start_time < capture_duration:
        contacts = reader.read_contacts()
        
        if contacts is not None and len(contacts) > 0:
            # Store sample
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
            gesture_samples.append(sample)
            
            # Print progress every 0.5 seconds
            if time.time() - last_print_time > 0.5:
                print(f"  Capturing... {len(gesture_samples)} samples, {len(contacts)} finger(s)")
                last_print_time = time.time()
        
        time.sleep(0.016)  # 60 FPS
    
    print()
    print(f"✓ Captured {len(gesture_samples)} samples")
    print()
    
    # Extract features
    if gesture_samples:
        features = extract_simple_features(gesture_samples)
        
        print("="*60)
        print("Biometric Features Extracted:")
        print("="*60)
        for key, value in features.items():
            print(f"  {key:20s}: {value:.2f}")
        print("="*60)
        print()
        print("✓ Success! Windows touchpad integration working!")
    else:
        print("✗ No samples captured. Did you touch the touchpad?")
    
    # Cleanup
    reader.stop()
    print()
    print("✓ Test complete")


if __name__ == "__main__":
    main()
