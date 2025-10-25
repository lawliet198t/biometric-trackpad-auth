#!/usr/bin/env python3
"""
Windows Biometric Trainer

Simple biometric authentication trainer for Windows touchpad.
Uses the Raw Input API to capture multi-touch gestures.

Usage:
    1. Run this script
    2. Perform your gesture 5 times (training)
    3. Try to authenticate with the same gesture
"""

import time
import numpy as np
from simple_windows_touchpad import SimpleTouchpadReader
from typing import List, Dict
import pickle


class WindowsBiometricTrainer:
    """Simple biometric trainer for Windows touchpad"""
    
    def __init__(self, training_samples: int = 5):
        self.training_samples = training_samples
        self.training_features = []
        self.baseline = None
        self.reader = None
    
    def extract_features(self, gesture_samples: List[Dict]) -> np.ndarray:
        """
        Extract biometric features from gesture samples
        
        Features:
        - Duration
        - Number of fingers
        - Average velocity per finger
        - Max velocity
        - Path length
        - Coordinate variance
        """
        if not gesture_samples:
            return np.array([])
        
        features = []
        
        # 1. Duration
        if len(gesture_samples) > 1:
            duration = gesture_samples[-1]['time'] - gesture_samples[0]['time']
        else:
            duration = 0
        features.append(duration)
        
        # 2. Number of fingers
        all_contact_ids = set()
        for sample in gesture_samples:
            for contact in sample['contacts']:
                all_contact_ids.add(contact['id'])
        num_fingers = len(all_contact_ids)
        features.append(num_fingers)
        
        # 3. Per-finger features
        for contact_id in sorted(all_contact_ids):
            positions = []
            times = []
            
            for sample in gesture_samples:
                for contact in sample['contacts']:
                    if contact['id'] == contact_id:
                        positions.append((contact['x'], contact['y']))
                        times.append(sample['time'])
            
            if len(positions) > 1:
                # Velocity
                total_distance = 0
                for i in range(1, len(positions)):
                    dx = positions[i][0] - positions[i-1][0]
                    dy = positions[i][1] - positions[i-1][1]
                    distance = np.sqrt(dx**2 + dy**2)
                    total_distance += distance
                
                total_time = times[-1] - times[0]
                velocity = total_distance / total_time if total_time > 0 else 0
                features.append(velocity)
                
                # Path length
                features.append(total_distance)
                
                # Coordinate variance
                xs = [p[0] for p in positions]
                ys = [p[1] for p in positions]
                features.append(np.var(xs))
                features.append(np.var(ys))
            else:
                features.extend([0, 0, 0, 0])
        
        # Pad to fixed size (assume max 5 fingers)
        while len(features) < 2 + 5 * 4:  # duration + num_fingers + 5 fingers * 4 features
            features.append(0)
        
        return np.array(features[:22])  # Fixed size
    
    def capture_gesture(self, duration: float = 2.0) -> List[Dict]:
        """Capture a gesture for specified duration"""
        print(f"\n👆 Touch your touchpad NOW for {duration} seconds...")
        print("   (Use 2-3 fingers and move them in your pattern)")
        
        gesture_samples = []
        start_time = time.time()
        last_contact_count = 0
        
        while time.time() - start_time < duration:
            contacts = self.reader.read_contacts()
            
            if contacts is not None and len(contacts) > 0:
                sample = {
                    'time': time.time(),
                    'contacts': [
                        {'id': c['ContactId'], 'x': c['X'], 'y': c['Y']}
                        for c in contacts
                    ]
                }
                gesture_samples.append(sample)
                
                if len(contacts) != last_contact_count:
                    print(f"   {len(contacts)} finger(s) detected...")
                    last_contact_count = len(contacts)
            
            time.sleep(0.016)
        
        print(f"✓ Captured {len(gesture_samples)} samples")
        return gesture_samples
    
    def train(self):
        """Train the biometric baseline"""
        print("\n" + "="*60)
        print("TRAINING MODE")
        print("="*60)
        print(f"\nYou need to perform your gesture {self.training_samples} times.")
        print("Try to be consistent!")
        
        for i in range(self.training_samples):
            print(f"\n--- Training Sample {i+1}/{self.training_samples} ---")
            input("Press ENTER when ready...")
            
            gesture = self.capture_gesture()
            
            if len(gesture) < 10:
                print("⚠️  Too few samples. Try again.")
                i -= 1
                continue
            
            features = self.extract_features(gesture)
            self.training_features.append(features)
            
            print(f"✓ Sample {i+1} recorded")
        
        # Calculate baseline
        self.baseline = {
            'mean': np.mean(self.training_features, axis=0),
            'std': np.std(self.training_features, axis=0) + 1e-6  # Avoid division by zero
        }
        
        print("\n" + "="*60)
        print("✓ Training Complete!")
        print("="*60)
        print(f"\nBaseline established from {self.training_samples} samples")
        
        # Save baseline
        with open('windows_baseline.pkl', 'wb') as f:
            pickle.dump(self.baseline, f)
        print("✓ Baseline saved to windows_baseline.pkl")
    
    def verify(self, gesture_samples: List[Dict]) -> tuple:
        """
        Verify a gesture against the baseline
        
        Returns:
            (is_authentic, confidence, distance)
        """
        if self.baseline is None:
            return False, 0.0, float('inf')
        
        features = self.extract_features(gesture_samples)
        
        # Calculate normalized distance
        diff = features - self.baseline['mean']
        normalized_diff = diff / self.baseline['std']
        distance = np.linalg.norm(normalized_diff)
        
        # Threshold (tune this based on your needs)
        threshold = 3.0  # 3 standard deviations
        
        is_authentic = distance < threshold
        confidence = max(0, 1 - (distance / threshold))
        
        return is_authentic, confidence, distance
    
    def test(self):
        """Test authentication"""
        if self.baseline is None:
            print("✗ No baseline found. Train first!")
            return
        
        print("\n" + "="*60)
        print("VERIFICATION MODE")
        print("="*60)
        print("\nPerform your gesture to authenticate.")
        
        while True:
            print("\n--- Verification Attempt ---")
            choice = input("Press ENTER to try, or 'q' to quit: ")
            
            if choice.lower() == 'q':
                break
            
            gesture = self.capture_gesture()
            
            if len(gesture) < 10:
                print("⚠️  Too few samples. Try again.")
                continue
            
            is_authentic, confidence, distance = self.verify(gesture)
            
            print("\n" + "="*60)
            if is_authentic:
                print("✓ AUTHENTICATED")
                print(f"  Confidence: {confidence*100:.1f}%")
                print(f"  Distance: {distance:.2f}")
            else:
                print("✗ REJECTED")
                print(f"  Confidence: {confidence*100:.1f}%")
                print(f"  Distance: {distance:.2f} (threshold: 3.0)")
            print("="*60)
    
    def run(self):
        """Main run loop"""
        print("\n" + "="*60)
        print("Windows Biometric Authentication Trainer")
        print("="*60)
        print("\nMake sure the TouchpadCapture window is open!")
        print("(It should be always-on-top in the corner)")
        
        # Start reader
        self.reader = SimpleTouchpadReader()
        
        if not self.reader.start():
            print("\n✗ Failed to start touchpad reader")
            print("  Make sure TouchpadCapture.exe is built")
            print("  Run: build_rawinput.bat")
            return
        
        print("\n✓ Touchpad reader started")
        time.sleep(1)
        
        # Check if baseline exists
        try:
            with open('windows_baseline.pkl', 'rb') as f:
                self.baseline = pickle.load(f)
            print("✓ Loaded existing baseline")
            
            choice = input("\nTrain new baseline (t) or Test existing (enter)? ")
            if choice.lower() == 't':
                self.train()
        except FileNotFoundError:
            print("ℹ️  No existing baseline found")
            self.train()
        
        # Test mode
        self.test()
        
        # Cleanup
        self.reader.stop()
        print("\n✓ Done!")


def main():
    trainer = WindowsBiometricTrainer(training_samples=5)
    trainer.run()


if __name__ == "__main__":
    main()
