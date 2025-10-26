#!/usr/bin/env python3
"""
Advanced Real-Time Biometric Verifier

Uses pure motion dynamics (X, Y, Timestamp only):
- Velocity, Acceleration, Jerk (smoothness)
- Curvature (path shape)
- Hesitation detection (micro-pauses)
- Multi-stage verification with strict gating

No pressure or contact area needed!
"""

import asyncio
import numpy as np
from typing import List, Dict
import pygame

# Import our libraries
from trackpad_lib import TrackpadCapture, GestureVisualizer, GestureTrack, TouchPoint, run_capture_loop
from advanced_biometrics import AdvancedFeatureExtractor, BiometricBaseline, MultiStageVerifier


class AdvancedBiometricVerifier:
    """
    Real-time verifier using advanced biometric features.
    
    Workflow:
    1. Collect N training samples
    2. Learn biometric baseline
    3. Verify new gestures with multi-stage gating
    """
    
    def __init__(self, training_samples: int = 10):
        self.training_samples = training_samples
        self.is_training_mode = True
        
        # Feature extraction
        self.extractor = AdvancedFeatureExtractor()
        
        # Training data
        self.training_features = []
        
        # Baseline and verifier
        self.baseline = BiometricBaseline()
        self.verifier = None
        
        # Current verification result
        self.last_verification = None
        self.last_features = None
    
    def add_training_sample(self, tracks: List[GestureTrack]) -> bool:
        """Add a training sample"""
        if not tracks or len(tracks[0].points) < 5:  # Reduced from 10 to 5
            print("⚠️  Gesture too short, skipped")
            return False
        
        primary_track = tracks[0]
        
        # Extract features
        features = self.extractor.extract_all_dynamics(primary_track.points)
        
        # Basic validation - allow very fast gestures (0.05s minimum)
        if features['duration'] < 0.05 or features['duration'] > 10.0:
            print(f"⚠️  Duration out of range ({features['duration']:.2f}s), skipped")
            print(f"   Hint: Gesture must be between 0.05s and 10s")
            return False
        
        self.training_features.append(features)
        
        print(f"✓ Training sample {len(self.training_features)}/{self.training_samples} captured")
        print(f"  Duration: {features['duration']:.3f}s ({features['point_count']} points)")
        print(f"  Path: {features['path_length']:.0f}px")
        print(f"  Velocity CV: {features['velocity_cv']:.3f}")
        print(f"  Jerk CV: {features['jerk_cv']:.3f}")
        print(f"  Hesitations: {features['hesitation_count']}")
        
        return True
    
    def train_baseline(self) -> bool:
        """Train the biometric baseline"""
        if len(self.training_features) < 3:
            print("❌ Need at least 3 training samples")
            return False
        
        print(f"\n🎓 Learning biometric baseline from {len(self.training_features)} samples...")
        
        # Learn baseline
        success = self.baseline.learn_from_samples(self.training_features)
        
        if success:
            # Create verifier
            self.verifier = MultiStageVerifier(self.baseline)
            self.is_training_mode = False
            
            # Save baseline
            import pickle
            baseline_file = 'baseline.pkl'
            with open(baseline_file, 'wb') as f:
                pickle.dump(self.baseline, f)
            print(f"\n✓ Baseline saved to {baseline_file}")
            print("\n✓ Baseline learned! Ready to verify.")
            print(f"\nTo use this baseline later:")
            print(f"  python3 realtime_verify.py --baseline {baseline_file}")
            return True
        
        return False
    
    def verify(self, tracks: List[GestureTrack]) -> Dict:
        """Verify a gesture"""
        if self.verifier is None:
            return None
        
        if not tracks or len(tracks[0].points) < 5:  # Reduced from 10 to 5
            return None
        
        primary_track = tracks[0]
        
        # Extract features
        features = self.extractor.extract_all_dynamics(primary_track.points)
        self.last_features = features
        
        # Verify
        result = self.verifier.verify(features)
        self.last_verification = result
        
        return result


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Advanced Biometric Verifier")
    parser.add_argument('--device', default=None, help='Input device (auto-detects if not specified)')
    parser.add_argument('--samples', type=int, default=10, help='Training samples')
    args = parser.parse_args()
    
    # Create instances (C# window now has its own visualization!)
    capture = TrackpadCapture(device_path=args.device, headless=False)
    visualizer = GestureVisualizer(
        width=1200,
        height=800,
        title="Advanced Biometric Verifier"
    )
    verifier = AdvancedBiometricVerifier(training_samples=args.samples)
    
    # Callback when gesture complete
    async def on_gesture_complete(tracks):
        if verifier.is_training_mode:
            # Training mode
            if verifier.add_training_sample(tracks):
                if len(verifier.training_features) >= verifier.training_samples:
                    # Train baseline
                    if verifier.train_baseline():
                        visualizer.set_status("READY TO VERIFY", (0, 255, 0))
                        print("\n✓ Training complete! Now draw gestures to verify.")
                        print("  Press SPACE to capture and verify")
                else:
                    remaining = verifier.training_samples - len(verifier.training_features)
                    visualizer.set_status(f"TRAINING ({remaining} more)", (255, 165, 0))
        else:
            # Verification mode
            result = verifier.verify(tracks)
            if result:
                passed = result['passed']
                color = (0, 255, 0) if passed else (255, 0, 0)
                visualizer.set_status(
                    f"{'✓ PASS' if passed else '✗ FAIL'} ({result['overall_score']:.1f}%)",
                    color
                )
                
                # Detailed console output
                print(f"\n{'='*60}")
                print(f"{'✓ VERIFICATION PASSED' if passed else '✗ VERIFICATION FAILED'}")
                print(f"{'='*60}")
                print(f"Overall Score: {result['overall_score']:.1f}%")
                print(f"Stage Reached: {result['stage_reached']}/3")
                
                print(f"\nStage 1 (Gatekeeper): {'✓ PASS' if result['stage1_passed'] else '✗ FAIL'}")
                print(f"  Score: {result['stage1_score']:.1f}%")
                print(f"  Reason: {result['stage1_reason']}")
                
                if result['stage_reached'] >= 3:
                    print(f"\nStage 3 (Dynamics): {'✓ PASS' if result['stage3_passed'] else '✗ FAIL'}")
                    print(f"  Score: {result['stage3_score']:.1f}%")
                    print(f"  Reason: {result['stage3_reason']}")
                
                # Feature details
                features = verifier.last_features
                if features:
                    print(f"\nGesture Metrics:")
                    print(f"  Duration: {features['duration']:.3f}s (baseline: {verifier.baseline.duration_mean:.3f}±{verifier.baseline.duration_std:.3f}s)")
                    print(f"  Path: {features['path_length']:.0f}px (baseline: {verifier.baseline.path_length_mean:.0f}±{verifier.baseline.path_length_std:.0f}px)")
                    print(f"  Velocity CV: {features['velocity_cv']:.3f} (baseline: {verifier.baseline.velocity_cv_mean:.3f}±{verifier.baseline.velocity_cv_std:.3f})")
                    print(f"  Jerk CV: {features['jerk_cv']:.3f} (baseline: {verifier.baseline.jerk_cv_mean:.3f}±{verifier.baseline.jerk_cv_std:.3f})")
                    print(f"  Hesitations: {features['hesitation_count']} (baseline: {verifier.baseline.hesitation_count_mean:.1f}±{verifier.baseline.hesitation_count_std:.1f})")
    
    # Custom UI
    def draw_custom_ui(screen, font, small_font, tiny_font):
        panel_x = screen.get_width() - 450
        panel_y = 80
        
        if verifier.is_training_mode:
            # Training progress
            progress = len(verifier.training_features) / verifier.training_samples
            text = small_font.render(f"Training: {len(verifier.training_features)}/{verifier.training_samples}", True, (255, 200, 0))
            screen.blit(text, (panel_x, panel_y))
            
            # Progress bar
            bar_width = 400
            bar_height = 25
            pygame.draw.rect(screen, (50, 50, 50), (panel_x, panel_y + 30, bar_width, bar_height))
            pygame.draw.rect(screen, (0, 255, 0), (panel_x, panel_y + 30, int(bar_width * progress), bar_height))
            
            # Instructions
            panel_y += 70
            lines = [
                "Draw your gesture consistently",
                "Press SPACE after each gesture",
                "",
                "What's being captured:",
                "  • Velocity patterns",
                "  • Acceleration profile",
                "  • Jerk (smoothness)",
                "  • Hesitation patterns",
                "  • Duration & path"
            ]
            for line in lines:
                inst = tiny_font.render(line, True, (150, 150, 150))
                screen.blit(inst, (panel_x, panel_y))
                panel_y += 18
        else:
            # Verification results
            if verifier.last_verification:
                result = verifier.last_verification
                features = verifier.last_features
                
                # Result header
                passed = result['passed']
                color = (0, 255, 0) if passed else (255, 0, 0)
                result_text = font.render('✓ PASS' if passed else '✗ FAIL', True, color)
                screen.blit(result_text, (panel_x, panel_y))
                panel_y += 50
                
                # Overall score
                score_text = small_font.render(f"Score: {result['overall_score']:.1f}%", True, color)
                screen.blit(score_text, (panel_x, panel_y))
                panel_y += 35
                
                # Stage results
                stage1_color = (0, 255, 0) if result['stage1_passed'] else (255, 0, 0)
                stage1_text = tiny_font.render(
                    f"Stage 1 (Gatekeeper): {'✓' if result['stage1_passed'] else '✗'} {result['stage1_score']:.0f}%",
                    True, stage1_color
                )
                screen.blit(stage1_text, (panel_x, panel_y))
                panel_y += 20
                
                if result['stage_reached'] >= 3:
                    stage3_color = (0, 255, 0) if result['stage3_passed'] else (255, 0, 0)
                    stage3_text = tiny_font.render(
                        f"Stage 3 (Dynamics): {'✓' if result['stage3_passed'] else '✗'} {result['stage3_score']:.0f}%",
                        True, stage3_color
                    )
                    screen.blit(stage3_text, (panel_x, panel_y))
                    panel_y += 20
                
                panel_y += 15
                
                # Feature comparison
                if features:
                    baseline = verifier.baseline
                    
                    header = small_font.render("Biometric Analysis:", True, (100, 200, 255))
                    screen.blit(header, (panel_x, panel_y))
                    panel_y += 30
                    
                    # Duration
                    duration_sigma = abs(features['duration'] - baseline.duration_mean) / baseline.duration_std if baseline.duration_std > 0 else 0
                    duration_color = (0, 255, 0) if duration_sigma < 2.0 else (255, 165, 0) if duration_sigma < 3.0 else (255, 0, 0)
                    duration_text = tiny_font.render(
                        f"⏱️  Duration: {features['duration']:.2f}s (σ={duration_sigma:.1f})",
                        True, duration_color
                    )
                    screen.blit(duration_text, (panel_x, panel_y))
                    panel_y += 18
                    
                    # Velocity CV
                    vel_sigma = abs(features['velocity_cv'] - baseline.velocity_cv_mean) / baseline.velocity_cv_std if baseline.velocity_cv_std > 0 else 0
                    vel_color = (0, 255, 0) if vel_sigma < 2.0 else (255, 165, 0) if vel_sigma < 3.0 else (255, 0, 0)
                    vel_text = tiny_font.render(
                        f"🏃 Velocity CV: {features['velocity_cv']:.3f} (σ={vel_sigma:.1f})",
                        True, vel_color
                    )
                    screen.blit(vel_text, (panel_x, panel_y))
                    panel_y += 18
                    
                    # Jerk CV (CRITICAL)
                    jerk_sigma = abs(features['jerk_cv'] - baseline.jerk_cv_mean) / baseline.jerk_cv_std if baseline.jerk_cv_std > 0 else 0
                    jerk_color = (0, 255, 0) if jerk_sigma < 2.0 else (255, 165, 0) if jerk_sigma < 3.0 else (255, 0, 0)
                    jerk_text = tiny_font.render(
                        f"⚡ Jerk CV: {features['jerk_cv']:.3f} (σ={jerk_sigma:.1f})",
                        True, jerk_color
                    )
                    screen.blit(jerk_text, (panel_x, panel_y))
                    panel_y += 18
                    
                    # Hesitations
                    hes_sigma = abs(features['hesitation_count'] - baseline.hesitation_count_mean) / baseline.hesitation_count_std if baseline.hesitation_count_std > 0 else 0
                    hes_color = (0, 255, 0) if hes_sigma < 2.0 else (255, 165, 0) if hes_sigma < 3.0 else (255, 0, 0)
                    hes_text = tiny_font.render(
                        f"⏸️  Hesitations: {features['hesitation_count']} (σ={hes_sigma:.1f})",
                        True, hes_color
                    )
                    screen.blit(hes_text, (panel_x, panel_y))
    
    visualizer.set_custom_ui_callback(draw_custom_ui)
    
    # Initial status
    visualizer.set_status(f"TRAINING (0/{args.samples})", (255, 165, 0))
    visualizer.set_info_lines([
        f"Collect {args.samples} training samples",
        "Draw your gesture and press SPACE",
        "Baseline will be learned automatically"
    ])
    
    print(f"Advanced Biometric Verifier")
    print(f"=" * 60)
    print(f"Training samples: {args.samples}")
    print(f"\nPure Dynamics Approach (X, Y, Timestamp only):")
    print(f"  ⏱️  Duration gating (STRICT)")
    print(f"  🏃 Velocity patterns")
    print(f"  🚀 Acceleration profile")
    print(f"  ⚡ Jerk analysis (smoothness - CRITICAL)")
    print(f"  ⏸️  Hesitation detection")
    print(f"  📐 Curvature analysis")
    print(f"\nGesture Requirements:")
    print(f"  • Duration: 0.05s - 10s (aim for 0.5-3s)")
    print(f"  • Points: At least 5 (more is better)")
    print(f"  • Consistency: Try to repeat the same way")
    print(f"\nDraw your gesture {args.samples} times (press SPACE each time)")
    print(f"Baseline will be learned automatically after {args.samples} samples")
    print(f"\n💡 Tip: If gestures are being skipped, try:")
    print(f"   1. Draw slower (keep finger on trackpad longer)")
    print(f"   2. Draw a longer path")
    print(f"   3. Use debug_capture.py to see what's being captured")
    
    # Run
    await run_capture_loop(capture, visualizer, on_gesture_complete)


if __name__ == "__main__":
    asyncio.run(main())
