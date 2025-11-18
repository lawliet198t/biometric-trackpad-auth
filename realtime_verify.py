#!/usr/bin/env python3
"""
Real-Time Verification with Live Display

Load a pre-trained baseline and verify gestures with real-time metrics display.

Usage:
  python3 realtime_verify.py --baseline baseline.json

Shows live updates as you draw:
- Duration, points, path length
- Velocity CV, Jerk CV, Hesitations
- Live verification scores (Stage 1, Stage 3, Overall)
"""

import asyncio
import time
import numpy as np
import pygame
import json
import sys
from typing import Dict, List

from trackpad_lib import TrackpadCapture, GestureVisualizer, GestureTrack, run_capture_loop
from advanced_biometrics import AdvancedFeatureExtractor, BiometricBaseline, MultiStageVerifier


class RealtimeVerifier:
    """Real-time verifier with live display - loads pre-trained baseline"""
    
    def __init__(self, baseline_path: str, verbose: bool = False):
        self.baseline_path = baseline_path
        self.extractor = AdvancedFeatureExtractor()
        self.verbose = verbose  # Control detailed logging
        
        # Load baseline
        self.baseline = self.load_baseline(baseline_path)
        self.verifier = MultiStageVerifier(self.baseline)
        
        # Verification results
        self.last_verification = None
        self.last_features = None
        
        # Real-time metrics (updated during drawing)
        self.realtime_metrics = {
            'duration': 0.0,
            'point_count': 0,
            'path_length': 0.0,
            'velocity_cv': 0.0,
            'jerk_cv': 0.0,
            'hesitation_count': 0,
            'stage1_score': 0.0,
            'stage3_score': 0.0,
            'overall_score': 0.0,
            'is_verifying': False
        }
        
        # Real-time verification settings
        self.min_points_for_realtime = 10
        self.last_realtime_verify = 0
        self.realtime_verify_interval = 0.15  # Verify every 150ms
        
        # Console output throttling
        self.last_console_print = 0
        self.console_print_interval = 1.0  # Print detailed logs max once per second
    
    def load_baseline(self, path: str) -> BiometricBaseline:
        """Load baseline from file"""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                baseline = BiometricBaseline.from_dict(data)
            
            print(f"✓ Loaded baseline from {path}")
            print(f"  Duration: {baseline.duration_mean:.3f}s ± {baseline.duration_std:.3f}s")
            print(f"  Jerk CV: {baseline.jerk_cv_mean:.3f} ± {baseline.jerk_cv_std:.3f}")
            print(f"  Hesitations: {baseline.hesitation_count_mean:.1f} ± {baseline.hesitation_count_std:.1f}")
            
            return baseline
        except Exception as e:
            print(f"❌ Error loading baseline: {e}")
            print(f"\nTo create a baseline, run:")
            print(f"  python3 realtime_trainer.py --samples 10")
            print(f"  (This will save baseline.json automatically)")
            sys.exit(1)
    
    def update_realtime_metrics(self, tracks: List[GestureTrack]):
        """Update real-time metrics during drawing (with throttled logging)"""
        if not tracks or len(tracks[0].points) < 2:
            return
        
        primary_track = tracks[0]
        points = primary_track.points
        
        # Basic metrics
        self.realtime_metrics['point_count'] = len(points)
        self.realtime_metrics['duration'] = points[-1].timestamp - points[0].timestamp
        
        # Calculate path length
        path_length = 0.0
        for i in range(1, len(points)):
            dx = points[i].x - points[i-1].x
            dy = points[i].y - points[i-1].y
            path_length += np.sqrt(dx**2 + dy**2)
        self.realtime_metrics['path_length'] = path_length
        
        # If enough points, calculate advanced metrics
        if len(points) >= self.min_points_for_realtime:
            # Check if enough time has passed since last verification
            current_time = time.time()
            if current_time - self.last_realtime_verify >= self.realtime_verify_interval:
                self.last_realtime_verify = current_time
                
                # Extract features
                features = self.extractor.extract_all_dynamics(points)
                
                self.realtime_metrics['velocity_cv'] = features['velocity_cv']
                self.realtime_metrics['jerk_cv'] = features['jerk_cv']
                self.realtime_metrics['hesitation_count'] = features['hesitation_count']
                
                # Run real-time verification
                self.realtime_metrics['is_verifying'] = True
                result = self.verifier.verify(features)
                
                self.realtime_metrics['stage1_score'] = result['stage1_score']
                self.realtime_metrics['stage3_score'] = result['stage3_score']
                self.realtime_metrics['overall_score'] = result['overall_score']
                
                # Throttled verbose logging (only if enabled and interval passed)
                if self.verbose and (current_time - self.last_console_print >= self.console_print_interval):
                    self.last_console_print = current_time
                    print(f"[Realtime] Points: {len(points)}, Duration: {features['duration']:.2f}s, "
                          f"Jerk CV: {features['jerk_cv']:.2f}, Score: {result['overall_score']:.0f}%")
    
    def verify(self, tracks: List[GestureTrack]) -> Dict:
        """Verify a completed gesture"""
        if not tracks or len(tracks[0].points) < 5:
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
    parser = argparse.ArgumentParser(description="Real-Time Verifier with Display")
    parser.add_argument('--baseline', required=True, help='Baseline file (baseline.json)')
    parser.add_argument('--device', default=None, help='Input device (auto-detects if not specified)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose realtime logging (throttled to 1/sec)')
    args = parser.parse_args()
    
    # Create instances
    capture = TrackpadCapture(device_path=args.device)
    visualizer = GestureVisualizer(
        width=1400,
        height=900,
        title="Real-Time Verification with Display",
        auto_size=True  # Automatically adapt to touchpad dimensions
    )
    verifier = RealtimeVerifier(baseline_path=args.baseline, verbose=args.verbose)
    
    # Callback when gesture complete (only print on completion, not during realtime)
    async def on_gesture_complete(tracks):
        result = verifier.verify(tracks)
        if result:
            passed = result['passed']
            color = (0, 255, 0) if passed else (255, 0, 0)
            visualizer.set_status(
                f"{'✓ PASS' if passed else '✗ FAIL'} ({result['overall_score']:.1f}%)",
                color
            )
            
            # Detailed console output (only on gesture completion)
            print(f"\n{'='*60}")
            print(f"{'✓ VERIFICATION PASSED' if passed else '✗ VERIFICATION FAILED'}")
            print(f"{'='*60}")
            print(f"Overall Score: {result['overall_score']:.1f}%")
            
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
                print(f"  Velocity CV: {features['velocity_cv']:.3f} (baseline: {verifier.baseline.velocity_cv_mean:.3f}±{verifier.baseline.velocity_cv_std:.3f})")
                print(f"  Jerk CV: {features['jerk_cv']:.3f} (baseline: {verifier.baseline.jerk_cv_mean:.3f}±{verifier.baseline.jerk_cv_std:.3f})")
                print(f"  Hesitations: {features['hesitation_count']} (baseline: {verifier.baseline.hesitation_count_mean:.1f}±{verifier.baseline.hesitation_count_std:.1f})")
    
    # Custom UI with real-time metrics
    def draw_custom_ui(screen, font, small_font, tiny_font):
        panel_x = screen.get_width() - 550
        panel_y = 80
        
        metrics = verifier.realtime_metrics
        
        # Header
        header = small_font.render("Real-Time Metrics", True, (100, 200, 255))
        screen.blit(header, (panel_x, panel_y))
        panel_y += 35
        
        # Duration (live)
        duration_color = (0, 255, 0) if 0.05 < metrics['duration'] < 10.0 else (255, 165, 0)
        duration_text = tiny_font.render(
            f"⏱️  Duration: {metrics['duration']:.3f}s",
            True, duration_color
        )
        screen.blit(duration_text, (panel_x, panel_y))
        panel_y += 20
        
        # Point count (live)
        point_text = tiny_font.render(
            f"📍 Points: {metrics['point_count']}",
            True, (200, 200, 200)
        )
        screen.blit(point_text, (panel_x, panel_y))
        panel_y += 20
        
        # Path length (live)
        path_text = tiny_font.render(
            f"📏 Path: {metrics['path_length']:.0f}px",
            True, (200, 200, 200)
        )
        screen.blit(path_text, (panel_x, panel_y))
        panel_y += 25
        
        # Advanced metrics (after enough points)
        if metrics['point_count'] >= verifier.min_points_for_realtime:
            # Velocity CV (live)
            vel_text = tiny_font.render(
                f"🏃 Velocity CV: {metrics['velocity_cv']:.3f}",
                True, (150, 255, 150)
            )
            screen.blit(vel_text, (panel_x, panel_y))
            panel_y += 20
            
            # Jerk CV (live) - CRITICAL
            jerk_color = (0, 255, 0) if metrics['jerk_cv'] < 2.0 else (255, 165, 0) if metrics['jerk_cv'] < 3.0 else (255, 0, 0)
            jerk_text = tiny_font.render(
                f"⚡ Jerk CV: {metrics['jerk_cv']:.3f} ⭐",
                True, jerk_color
            )
            screen.blit(jerk_text, (panel_x, panel_y))
            panel_y += 20
            
            # Hesitations (live)
            hes_text = tiny_font.render(
                f"⏸️  Hesitations: {metrics['hesitation_count']}",
                True, (255, 200, 100)
            )
            screen.blit(hes_text, (panel_x, panel_y))
            panel_y += 25
            
            # Real-time verification scores
            if metrics['is_verifying']:
                panel_y += 10
                verify_header = small_font.render("Live Verification", True, (255, 200, 100))
                screen.blit(verify_header, (panel_x, panel_y))
                panel_y += 30
                
                # Stage 1 score
                stage1_color = (0, 255, 0) if metrics['stage1_score'] > 70 else (255, 165, 0) if metrics['stage1_score'] > 50 else (255, 0, 0)
                stage1_text = tiny_font.render(
                    f"Stage 1: {metrics['stage1_score']:.0f}%",
                    True, stage1_color
                )
                screen.blit(stage1_text, (panel_x, panel_y))
                panel_y += 20
                
                # Stage 3 score
                stage3_color = (0, 255, 0) if metrics['stage3_score'] > 70 else (255, 165, 0) if metrics['stage3_score'] > 50 else (255, 0, 0)
                stage3_text = tiny_font.render(
                    f"Stage 3: {metrics['stage3_score']:.0f}%",
                    True, stage3_color
                )
                screen.blit(stage3_text, (panel_x, panel_y))
                panel_y += 20
                
                # Overall score
                overall_color = (0, 255, 0) if metrics['overall_score'] > 70 else (255, 165, 0) if metrics['overall_score'] > 50 else (255, 0, 0)
                overall_text = small_font.render(
                    f"Overall: {metrics['overall_score']:.0f}%",
                    True, overall_color
                )
                screen.blit(overall_text, (panel_x, panel_y))
        else:
            waiting_text = tiny_font.render(
                f"Drawing... (need {verifier.min_points_for_realtime} points)",
                True, (150, 150, 150)
            )
            screen.blit(waiting_text, (panel_x, panel_y))
        
        # Final verification result (if available)
        if verifier.last_verification:
            panel_y = screen.get_height() - 250
            
            result = verifier.last_verification
            passed = result['passed']
            
            # Large result indicator
            result_color = (0, 255, 0) if passed else (255, 0, 0)
            result_text = font.render('✓ PASS' if passed else '✗ FAIL', True, result_color)
            screen.blit(result_text, (panel_x, panel_y))
            panel_y += 50
            
            # Overall score
            score_text = small_font.render(f"Score: {result['overall_score']:.1f}%", True, result_color)
            screen.blit(score_text, (panel_x, panel_y))
            panel_y += 35
            
            # Stage breakdown
            stage1_status = '✓' if result['stage1_passed'] else '✗'
            stage1_text = tiny_font.render(
                f"{stage1_status} Stage 1: {result['stage1_score']:.0f}%",
                True, (0, 255, 0) if result['stage1_passed'] else (255, 0, 0)
            )
            screen.blit(stage1_text, (panel_x, panel_y))
            panel_y += 20
            
            if result['stage_reached'] >= 3:
                stage3_status = '✓' if result['stage3_passed'] else '✗'
                stage3_text = tiny_font.render(
                    f"{stage3_status} Stage 3: {result['stage3_score']:.0f}%",
                    True, (0, 255, 0) if result['stage3_passed'] else (255, 0, 0)
                )
                screen.blit(stage3_text, (panel_x, panel_y))
    
    visualizer.set_custom_ui_callback(draw_custom_ui)
    
    # Hook to update real-time metrics during drawing
    original_render = visualizer.render
    def render_with_metrics(capture_obj):
        # Update metrics before rendering
        if capture_obj.is_capturing:
            all_tracks = list(capture_obj.gesture_tracks.values())
            if all_tracks:
                verifier.update_realtime_metrics(all_tracks)
        original_render(capture_obj)
    visualizer.render = render_with_metrics
    
    # Initial status
    visualizer.set_status("READY TO VERIFY", (0, 255, 0))
    visualizer.set_info_lines([
        "Draw your gesture",
        "Watch metrics update in REAL-TIME!",
        "Press SPACE when done for final verification",
        "",
        "Baseline loaded:",
        f"  Duration: {verifier.baseline.duration_mean:.2f}±{verifier.baseline.duration_std:.2f}s",
        f"  Jerk CV: {verifier.baseline.jerk_cv_mean:.2f}±{verifier.baseline.jerk_cv_std:.2f}"
    ])
    
    print(f"Real-Time Verification with Display")
    print(f"=" * 60)
    print(f"Baseline: {args.baseline}")
    print(f"\nDraw your gesture and watch metrics update in REAL-TIME!")
    print(f"Press SPACE when done for final verification")
    print(f"\nWhat you'll see:")
    print(f"  ⏱️  Duration (live)")
    print(f"  📍 Points (live)")
    print(f"  🏃 Velocity CV (live)")
    print(f"  ⚡ Jerk CV (live) - CRITICAL")
    print(f"  ⏸️  Hesitations (live)")
    print(f"  📊 Live verification scores")
    
    # Run
    await run_capture_loop(capture, visualizer, on_gesture_complete)


if __name__ == "__main__":
    asyncio.run(main())
