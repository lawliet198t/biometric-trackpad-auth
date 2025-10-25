#!/usr/bin/env python3
"""
Unified Biometric App - Single Window

Combines touchpad capture and biometric verification in one pygame window.
No separate TouchpadCapture window needed!
"""

import pygame
import time
import numpy as np
import pickle
from simple_windows_touchpad_v2 import SimpleTouchpadReaderV2
from typing import List, Dict, Optional


class UnifiedBiometricApp:
    """Single-window biometric app"""
    
    def __init__(self, width=1200, height=800):
        self.width = width
        self.height = height
        
        # Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Biometric Authentication - Touch your touchpad!")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Touchpad reader
        self.reader = SimpleTouchpadReaderV2(lift_timeout=0.1)
        
        # Gesture tracking
        self.gesture_tracks = {}  # {contact_id: [(x, y, time), ...]}
        self.completed_tracks = []
        self.is_capturing = False
        
        # Biometric
        self.baseline = None
        self.training_samples = []
        self.mode = "IDLE"  # IDLE, TRAINING, VERIFYING
        self.status_message = "Press SPACE to start training"
        self.status_color = (200, 200, 200)
        
        # Colors for fingers
        self.colors = [
            (0, 255, 136), (255, 136, 0), (136, 0, 255),
            (0, 255, 255), (255, 0, 136)
        ]
    
    def extract_features(self, tracks: List[List]) -> np.ndarray:
        """Extract biometric features from gesture tracks"""
        if not tracks:
            return np.array([])
        
        features = []
        
        # Duration
        all_times = []
        for track in tracks:
            all_times.extend([p[2] for p in track])
        
        if len(all_times) > 1:
            duration = max(all_times) - min(all_times)
        else:
            duration = 0
        features.append(duration)
        
        # Number of fingers
        features.append(len(tracks))
        
        # Per-finger features
        for track in tracks[:5]:  # Max 5 fingers
            if len(track) > 1:
                # Velocity
                total_dist = 0
                for i in range(1, len(track)):
                    dx = track[i][0] - track[i-1][0]
                    dy = track[i][1] - track[i-1][1]
                    total_dist += np.sqrt(dx**2 + dy**2)
                
                total_time = track[-1][2] - track[0][2]
                velocity = total_dist / total_time if total_time > 0 else 0
                features.append(velocity)
                features.append(total_dist)
                
                # Variance
                xs = [p[0] for p in track]
                ys = [p[1] for p in track]
                features.append(np.var(xs))
                features.append(np.var(ys))
            else:
                features.extend([0, 0, 0, 0])
        
        # Pad to fixed size
        while len(features) < 22:
            features.append(0)
        
        return np.array(features[:22])
    
    def verify(self, features: np.ndarray) -> tuple:
        """Verify features against baseline"""
        if self.baseline is None:
            return False, 0.0, float('inf')
        
        diff = features - self.baseline['mean']
        normalized_diff = diff / self.baseline['std']
        distance = np.linalg.norm(normalized_diff)
        
        threshold = 3.0
        is_authentic = distance < threshold
        confidence = max(0, 1 - (distance / threshold))
        
        return is_authentic, confidence, distance
    
    def draw(self):
        """Draw everything"""
        # Background
        self.screen.fill((20, 20, 40))
        
        # Title
        title = self.font.render("Biometric Authentication", True, (100, 200, 255))
        self.screen.blit(title, (20, 20))
        
        # Status
        status = self.small_font.render(f"Mode: {self.mode}", True, (150, 150, 150))
        self.screen.blit(status, (20, 60))
        
        message = self.small_font.render(self.status_message, True, self.status_color)
        self.screen.blit(message, (20, 90))
        
        # Draw gesture tracks
        for contact_id, track in self.gesture_tracks.items():
            if len(track) > 1:
                color = self.colors[contact_id % len(self.colors)]
                points = [(p[0], p[1]) for p in track]
                pygame.draw.lines(self.screen, color, False, points, 3)
        
        # Draw completed tracks (dimmed)
        for track in self.completed_tracks:
            if len(track) > 1:
                color = (100, 100, 100)
                points = [(p[0], p[1]) for p in track]
                pygame.draw.lines(self.screen, color, False, points, 2)
        
        # Instructions
        instructions = [
            "SPACE: Start/Stop capture",
            "T: Train (5 samples)",
            "V: Verify",
            "C: Clear",
            "Q: Quit"
        ]
        y = self.height - 120
        for inst in instructions:
            text = self.small_font.render(inst, True, (120, 120, 120))
            self.screen.blit(text, (20, y))
            y += 24
        
        pygame.display.flip()
    
    def update_gestures(self):
        """Update gesture tracking from touchpad"""
        contacts = self.reader.read_contacts()
        
        if contacts is not None and self.is_capturing:
            current_time = time.time()
            current_ids = set()
            
            if len(contacts) > 0:
                for contact in contacts:
                    contact_id = contact['ContactId']
                    x = contact['X'] / 65535.0 * self.width
                    y = contact['Y'] / 65535.0 * self.height
                    
                    current_ids.add(contact_id)
                    
                    if contact_id not in self.gesture_tracks:
                        self.gesture_tracks[contact_id] = []
                    
                    self.gesture_tracks[contact_id].append((x, y, current_time))
            
            # Detect lifted fingers
            lifted = set(self.gesture_tracks.keys()) - current_ids
            for contact_id in lifted:
                track = self.gesture_tracks[contact_id]
                if len(track) > 5:  # Minimum points
                    self.completed_tracks.append(track)
                del self.gesture_tracks[contact_id]
    
    def start_capture(self):
        """Start capturing gesture"""
        self.is_capturing = True
        self.gesture_tracks.clear()
        self.completed_tracks.clear()
        self.status_message = "Capturing... (Press SPACE to stop)"
        self.status_color = (0, 255, 0)
    
    def stop_capture(self):
        """Stop capturing and process gesture"""
        self.is_capturing = False
        
        # Move active tracks to completed
        for track in self.gesture_tracks.values():
            if len(track) > 5:
                self.completed_tracks.append(track)
        self.gesture_tracks.clear()
        
        # Process based on mode
        if self.mode == "TRAINING":
            if len(self.completed_tracks) > 0:
                features = self.extract_features(self.completed_tracks)
                self.training_samples.append(features)
                
                remaining = 5 - len(self.training_samples)
                if remaining > 0:
                    self.status_message = f"Sample {len(self.training_samples)}/5 recorded. {remaining} more needed."
                    self.status_color = (255, 200, 0)
                else:
                    # Training complete
                    self.baseline = {
                        'mean': np.mean(self.training_samples, axis=0),
                        'std': np.std(self.training_samples, axis=0) + 1e-6
                    }
                    with open('baseline.pkl', 'wb') as f:
                        pickle.dump(self.baseline, f)
                    
                    self.mode = "IDLE"
                    self.status_message = "Training complete! Press V to verify."
                    self.status_color = (0, 255, 0)
            else:
                self.status_message = "No gesture detected. Try again."
                self.status_color = (255, 100, 0)
        
        elif self.mode == "VERIFYING":
            if len(self.completed_tracks) > 0:
                features = self.extract_features(self.completed_tracks)
                is_auth, confidence, distance = self.verify(features)
                
                if is_auth:
                    self.status_message = f"✓ AUTHENTICATED ({confidence*100:.1f}%)"
                    self.status_color = (0, 255, 0)
                else:
                    self.status_message = f"✗ REJECTED ({confidence*100:.1f}%)"
                    self.status_color = (255, 0, 0)
                
                self.mode = "IDLE"
            else:
                self.status_message = "No gesture detected. Try again."
                self.status_color = (255, 100, 0)
                self.mode = "IDLE"
    
    def run(self):
        """Main loop"""
        if not self.reader.start():
            print("Failed to start touchpad reader")
            return
        
        # Try to load existing baseline
        try:
            with open('baseline.pkl', 'rb') as f:
                self.baseline = pickle.load(f)
            self.status_message = "Baseline loaded. Press V to verify or T to retrain."
        except FileNotFoundError:
            pass
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if not self.is_capturing:
                            self.start_capture()
                        else:
                            self.stop_capture()
                    
                    elif event.key == pygame.K_t:
                        self.mode = "TRAINING"
                        self.training_samples = []
                        self.status_message = "Training mode. Perform gesture 5 times (SPACE to capture)"
                        self.status_color = (255, 200, 0)
                    
                    elif event.key == pygame.K_v:
                        if self.baseline is None:
                            self.status_message = "No baseline! Press T to train first."
                            self.status_color = (255, 100, 0)
                        else:
                            self.mode = "VERIFYING"
                            self.status_message = "Verification mode. Perform your gesture (SPACE to capture)"
                            self.status_color = (100, 200, 255)
                    
                    elif event.key == pygame.K_c:
                        self.gesture_tracks.clear()
                        self.completed_tracks.clear()
                        self.status_message = "Cleared"
                        self.status_color = (150, 150, 150)
                    
                    elif event.key == pygame.K_q:
                        running = False
            
            self.update_gestures()
            self.draw()
            self.clock.tick(60)
        
        self.reader.stop()
        pygame.quit()


if __name__ == "__main__":
    app = UnifiedBiometricApp()
    app.run()
