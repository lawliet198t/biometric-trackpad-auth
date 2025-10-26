#!/usr/bin/env python3
"""
Unified Biometric Trainer

Single pygame window showing:
1. Real-time touchpad visualization
2. Training progress
3. Verification results
4. Biometric analysis

No separate C# window!
"""

import pygame
import time
import numpy as np
from simple_windows_touchpad import SimpleTouchpadReader
from typing import List, Dict, Optional
import pickle


class BiometricFeatureExtractor:
    """Extract biometric features from gesture samples"""
    
    @staticmethod
    def extract_features(gesture_samples: List[Dict]) -> np.ndarray:
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
        while len(features) < 2 + 5 * 4:
            features.append(0)
        
        return np.array(features[:22])


class UnifiedBiometricTrainer:
    """Unified window for biometric training and verification"""
    
    def __init__(self, width: int = 1400, height: int = 900, training_samples: int = 5):
        pygame.init()
        
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Unified Biometric Trainer")
        
        # Fonts
        self.font_huge = pygame.font.Font(None, 72)
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Colors
        self.bg_color = (20, 20, 30)
        self.panel_color = (30, 30, 40)
        self.text_color = (200, 200, 200)
        self.accent_color = (0, 255, 100)
        self.warning_color = (255, 165, 0)
        self.error_color = (255, 50, 50)
        self.contact_colors = [
            (255, 100, 100), (100, 255, 100), (100, 100, 255),
            (255, 255, 100), (255, 100, 255)
        ]
        
        # Touchpad reader (headless!)
        self.reader = SimpleTouchpadReader(headless=True)
        
        # Visualization
        self.contact_trails: Dict[int, List[tuple]] = {}
        self.trail_max_age = 2.0
        self.trail_max_points = 200
        
        # Touchpad bounds
        self.touchpad_min_x = 0
        self.touchpad_max_x = 10000
        self.touchpad_min_y = 0
        self.touchpad_max_y = 10000
        
        # Layout
        self.viz_area = pygame.Rect(20, 20, width - 520, height - 40)
        self.info_panel = pygame.Rect(width - 480, 20, 460, height - 40)
        
        # Biometric state
        self.mode = "training"  # "training" or "verification"
        self.training_samples = training_samples
        self.training_features = []
        self.baseline = None
        
        # Gesture capture
        self.capturing = False
        self.capture_start_time = 0
        self.capture_duration = 2.0
        self.current_gesture = []
        
        # Status
        self.status_text = "Ready to Train"
        self.status_color = self.accent_color
        self.message = "Press SPACE to start capturing"
        self.message_color = self.text_color
        
        # Verification result
        self.last_verification = None
        
        # FPS
        self.clock = pygame.time.Clock()
        self.fps = 0
    
    def start(self) -> bool:
        """Start the touchpad reader"""
        return self.reader.start()
    
    def stop(self):
        """Stop the touchpad reader"""
        self.reader.stop()
    
    def map_touchpad_to_screen(self, x: int, y: int) -> tuple:
        """Map touchpad coordinates to screen"""
        norm_x = (x - self.touchpad_min_x) / (self.touchpad_max_x - self.touchpad_min_x)
        norm_y = (y - self.touchpad_min_y) / (self.touchpad_max_y - self.touchpad_min_y)
        norm_x = max(0, min(1, norm_x))
        norm_y = max(0, min(1, norm_y))
        screen_x = self.viz_area.x + norm_x * self.viz_area.width
        screen_y = self.viz_area.y + norm_y * self.viz_area.height
        return int(screen_x), int(screen_y)
    
    def update_trails(self, contacts: List[Dict]):
        """Update contact trails"""
        current_time = time.time()
        
        for contact in contacts:
            contact_id = contact['ContactId']
            
            # Update bounds
            self.touchpad_min_x = min(self.touchpad_min_x, contact['X'])
            self.touchpad_max_x = max(self.touchpad_max_x, contact['X'])
            self.touchpad_min_y = min(self.touchpad_min_y, contact['Y'])
            self.touchpad_max_y = max(self.touchpad_max_y, contact['Y'])
            
            # Add to trail
            if contact_id not in self.contact_trails:
                self.contact_trails[contact_id] = []
            
            screen_pos = self.map_touchpad_to_screen(contact['X'], contact['Y'])
            self.contact_trails[contact_id].append((*screen_pos, current_time))
            
            if len(self.contact_trails[contact_id]) > self.trail_max_points:
                self.contact_trails[contact_id].pop(0)
        
        # Remove old points
        for contact_id in list(self.contact_trails.keys()):
            trail = self.contact_trails[contact_id]
            trail[:] = [(x, y, t) for x, y, t in trail if current_time - t < self.trail_max_age]
            if not trail:
                del self.contact_trails[contact_id]
    
    def capture_gesture_data(self, contacts: List[Dict]):
        """Capture gesture data during recording"""
        if not self.capturing:
            return
        
        if len(contacts) > 0:
            sample = {
                'time': time.time(),
                'contacts': [
                    {'id': c['ContactId'], 'x': c['X'], 'y': c['Y']}
                    for c in contacts
                ]
            }
            self.current_gesture.append(sample)
    
    def start_capture(self):
        """Start capturing a gesture"""
        self.capturing = True
        self.capture_start_time = time.time()
        self.current_gesture = []
        self.contact_trails.clear()
        self.status_text = "CAPTURING..."
        self.status_color = self.warning_color
        self.message = f"Perform your gesture now! ({self.capture_duration}s)"
        self.message_color = self.warning_color
    
    def finish_capture(self):
        """Finish capturing and process gesture"""
        self.capturing = False
        
        if len(self.current_gesture) < 10:
            self.status_text = "Too Short!"
            self.status_color = self.error_color
            self.message = "Gesture too short. Press SPACE to try again."
            self.message_color = self.error_color
            return
        
        if self.mode == "training":
            # Add training sample
            features = BiometricFeatureExtractor.extract_features(self.current_gesture)
            self.training_features.append(features)
            
            self.status_text = f"Sample {len(self.training_features)}/{self.training_samples}"
            self.status_color = self.accent_color
            
            if len(self.training_features) >= self.training_samples:
                # Train baseline
                self.train_baseline()
            else:
                remaining = self.training_samples - len(self.training_features)
                self.message = f"Good! {remaining} more samples needed. Press SPACE."
                self.message_color = self.accent_color
        
        elif self.mode == "verification":
            # Verify gesture
            self.verify_gesture()
    
    def train_baseline(self):
        """Train the biometric baseline"""
        self.baseline = {
            'mean': np.mean(self.training_features, axis=0),
            'std': np.std(self.training_features, axis=0) + 1e-6
        }
        
        # Save baseline
        with open('windows_baseline.pkl', 'wb') as f:
            pickle.dump(self.baseline, f)
        
        self.mode = "verification"
        self.status_text = "Training Complete!"
        self.status_color = self.accent_color
        self.message = "Now verify your gesture. Press SPACE."
        self.message_color = self.accent_color
    
    def verify_gesture(self):
        """Verify the captured gesture"""
        if self.baseline is None:
            return
        
        features = BiometricFeatureExtractor.extract_features(self.current_gesture)
        
        # Calculate normalized distance
        diff = features - self.baseline['mean']
        normalized_diff = diff / self.baseline['std']
        distance = np.linalg.norm(normalized_diff)
        
        threshold = 3.0
        is_authentic = distance < threshold
        confidence = max(0, 1 - (distance / threshold))
        
        self.last_verification = {
            'authentic': is_authentic,
            'confidence': confidence,
            'distance': distance,
            'threshold': threshold
        }
        
        if is_authentic:
            self.status_text = "✓ AUTHENTICATED"
            self.status_color = self.accent_color
            self.message = f"Confidence: {confidence*100:.1f}% | Distance: {distance:.2f}"
            self.message_color = self.accent_color
        else:
            self.status_text = "✗ REJECTED"
            self.status_color = self.error_color
            self.message = f"Confidence: {confidence*100:.1f}% | Distance: {distance:.2f}"
            self.message_color = self.error_color
    
    def draw_visualization(self):
        """Draw touchpad visualization"""
        pygame.draw.rect(self.screen, (40, 40, 50), self.viz_area)
        pygame.draw.rect(self.screen, (60, 60, 70), self.viz_area, 2)
        
        # Draw trails
        current_time = time.time()
        for contact_id, trail in self.contact_trails.items():
            if len(trail) < 2:
                continue
            
            color = self.contact_colors[contact_id % len(self.contact_colors)]
            
            for i in range(len(trail) - 1):
                x1, y1, t1 = trail[i]
                x2, y2, t2 = trail[i + 1]
                
                age = current_time - t2
                alpha = int(255 * (1 - age / self.trail_max_age))
                thickness = int(3 + 7 * (1 - age / self.trail_max_age))
                
                if alpha > 0:
                    pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), thickness)
            
            if trail:
                x, y, t = trail[-1]
                pygame.draw.circle(self.screen, color, (x, y), 20)
                pygame.draw.circle(self.screen, (255, 255, 255), (x, y), 20, 3)
                id_text = self.font_medium.render(str(contact_id), True, (255, 255, 255))
                self.screen.blit(id_text, (x - 10, y - 15))
        
        # Capture progress bar
        if self.capturing:
            elapsed = time.time() - self.capture_start_time
            progress = min(1.0, elapsed / self.capture_duration)
            
            bar_width = self.viz_area.width - 40
            bar_height = 30
            bar_x = self.viz_area.x + 20
            bar_y = self.viz_area.bottom - 50
            
            pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(self.screen, self.warning_color, (bar_x, bar_y, int(bar_width * progress), bar_height))
            pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), 2)
    
    def draw_info_panel(self):
        """Draw info panel"""
        pygame.draw.rect(self.screen, self.panel_color, self.info_panel)
        pygame.draw.rect(self.screen, (60, 60, 70), self.info_panel, 2)
        
        y = self.info_panel.y + 20
        
        # Title
        title = self.font_large.render("Biometric", True, self.accent_color)
        self.screen.blit(title, (self.info_panel.x + 20, y))
        y += 60
        
        # Mode
        mode_text = "TRAINING" if self.mode == "training" else "VERIFICATION"
        mode = self.font_medium.render(mode_text, True, self.text_color)
        self.screen.blit(mode, (self.info_panel.x + 20, y))
        y += 50
        
        # Status
        status = self.font_large.render(self.status_text, True, self.status_color)
        self.screen.blit(status, (self.info_panel.x + 20, y))
        y += 70
        
        # Message
        # Word wrap message
        words = self.message.split()
        line = ""
        for word in words:
            test_line = line + word + " "
            if self.font_small.size(test_line)[0] < self.info_panel.width - 40:
                line = test_line
            else:
                if line:
                    msg = self.font_small.render(line, True, self.message_color)
                    self.screen.blit(msg, (self.info_panel.x + 20, y))
                    y += 30
                line = word + " "
        if line:
            msg = self.font_small.render(line, True, self.message_color)
            self.screen.blit(msg, (self.info_panel.x + 20, y))
            y += 40
        
        # Training progress
        if self.mode == "training":
            progress = len(self.training_features) / self.training_samples
            bar_width = self.info_panel.width - 40
            bar_height = 30
            bar_x = self.info_panel.x + 20
            
            pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, y, bar_width, bar_height))
            pygame.draw.rect(self.screen, self.accent_color, (bar_x, y, int(bar_width * progress), bar_height))
            pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, y, bar_width, bar_height), 2)
            
            progress_text = f"{len(self.training_features)}/{self.training_samples}"
            prog = self.font_small.render(progress_text, True, (255, 255, 255))
            text_rect = prog.get_rect(center=(bar_x + bar_width // 2, y + bar_height // 2))
            self.screen.blit(prog, text_rect)
            y += 50
        
        # Verification result
        if self.mode == "verification" and self.last_verification:
            y += 20
            result = self.last_verification
            
            result_title = self.font_medium.render("Last Result:", True, self.text_color)
            self.screen.blit(result_title, (self.info_panel.x + 20, y))
            y += 40
            
            conf_text = f"Confidence: {result['confidence']*100:.1f}%"
            conf = self.font_small.render(conf_text, True, self.text_color)
            self.screen.blit(conf, (self.info_panel.x + 30, y))
            y += 30
            
            dist_text = f"Distance: {result['distance']:.2f}"
            dist = self.font_small.render(dist_text, True, self.text_color)
            self.screen.blit(dist, (self.info_panel.x + 30, y))
            y += 30
            
            thresh_text = f"Threshold: {result['threshold']:.2f}"
            thresh = self.font_small.render(thresh_text, True, self.text_color)
            self.screen.blit(thresh, (self.info_panel.x + 30, y))
        
        # Instructions
        y = self.info_panel.bottom - 150
        inst_title = self.font_small.render("Controls:", True, self.accent_color)
        self.screen.blit(inst_title, (self.info_panel.x + 20, y))
        y += 30
        
        instructions = [
            "SPACE - Capture gesture",
            "R - Reset training",
            "ESC - Exit"
        ]
        for line in instructions:
            inst = self.font_small.render(line, True, (150, 150, 150))
            self.screen.blit(inst, (self.info_panel.x + 30, y))
            y += 25
        
        # FPS
        fps_text = f"FPS: {self.fps:.0f}"
        fps = self.font_small.render(fps_text, True, (100, 100, 100))
        self.screen.blit(fps, (self.info_panel.x + 20, self.info_panel.bottom - 30))
    
    def run(self):
        """Main run loop"""
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE and not self.capturing:
                        self.start_capture()
                    elif event.key == pygame.K_r:
                        # Reset training
                        self.mode = "training"
                        self.training_features = []
                        self.baseline = None
                        self.last_verification = None
                        self.status_text = "Ready to Train"
                        self.status_color = self.accent_color
                        self.message = "Press SPACE to start capturing"
                        self.message_color = self.text_color
            
            # Read touchpad
            contacts_data = self.reader.read_contacts()
            
            if contacts_data is not None and len(contacts_data) > 0:
                self.update_trails(contacts_data)
                self.capture_gesture_data(contacts_data)
            
            # Check capture timeout
            if self.capturing and time.time() - self.capture_start_time >= self.capture_duration:
                self.finish_capture()
            
            # Draw
            self.screen.fill(self.bg_color)
            self.draw_visualization()
            self.draw_info_panel()
            pygame.display.flip()
            
            self.fps = self.clock.get_fps()
            self.clock.tick(60)


def main():
    print("="*60)
    print("Unified Biometric Trainer")
    print("="*60)
    print("\nSingle window with touchpad visualization!")
    print("(C# process runs in headless mode)\n")
    
    trainer = UnifiedBiometricTrainer(training_samples=5)
    
    if not trainer.start():
        print("✗ Failed to start touchpad reader")
        return
    
    print("✓ Touchpad reader started")
    print("\nControls:")
    print("  SPACE - Capture gesture")
    print("  R     - Reset training")
    print("  ESC   - Exit\n")
    
    try:
        trainer.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted...")
    finally:
        trainer.stop()
        pygame.quit()
        print("✓ Stopped")


if __name__ == "__main__":
    main()
