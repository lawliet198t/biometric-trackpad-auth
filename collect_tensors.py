#!/usr/bin/env python3
"""
Tensor Data Collector for Deep Learning Training

Replaces the old realtime_trainer.py for AI-based authentication.
Instead of extracting statistical features (velocity, jerk, etc.),
this script collects raw gesture tensors for neural network training.

Workflow:
1. Ask user for User ID / Label
2. Capture gestures interactively
3. Convert to fixed-length tensors (128, 3)
4. Save as .npy files for training

Output: data/raw/{user_id}_{timestamp}_{index}.npy
"""

import asyncio
import numpy as np
import os
import time
from pathlib import Path
from typing import List
import pygame

# Import our libraries
from trackpad_lib import TrackpadCapture, GestureVisualizer, GestureTrack, run_capture_loop
from tensor_processor import TensorProcessor, validate_tensor, SEQUENCE_LENGTH


class TensorCollector:
    """
    Collect and save gesture tensors for deep learning training.
    
    This replaces the old statistical feature extraction approach.
    Raw tensors are saved for future Siamese Network training.
    """
    
    def __init__(self, user_id: str, output_dir: str = "data/raw", 
                 target_samples: int = 50):
        """
        Initialize tensor collector.
        
        Args:
            user_id: User identifier (e.g., "alice", "bob")
            output_dir: Directory to save .npy files
            target_samples: Target number of samples to collect
        """
        self.user_id = user_id
        self.output_dir = Path(output_dir)
        self.target_samples = target_samples
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Tensor processor
        self.processor = TensorProcessor(
            sequence_length=SEQUENCE_LENGTH,
            normalization='standard'  # Use standard scaling for neural networks
        )
        
        # Collection state
        self.collected_tensors = []
        self.session_timestamp = int(time.time())
        
        print(f"✓ Tensor collector initialized")
        print(f"  User ID: {user_id}")
        print(f"  Output: {self.output_dir}")
        print(f"  Target: {target_samples} samples")
    
    def add_gesture(self, tracks: List[GestureTrack]) -> bool:
        """
        Process and save a gesture as a tensor.
        
        Args:
            tracks: List of GestureTrack objects (typically 1 finger)
        
        Returns:
            True if successfully saved, False otherwise
        """
        # Validate gesture
        if not tracks or len(tracks) == 0:
            print("⚠️  No tracks in gesture, skipped")
            return False
        
        # Use primary track (first finger)
        primary_track = tracks[0]
        
        # Check minimum points
        if len(primary_track.points) < 2:
            print(f"⚠️  Gesture too short ({len(primary_track.points)} points), skipped")
            return False
        
        # Convert to tensor
        try:
            tensor = primary_track.get_tensor_representation(
                sequence_length=SEQUENCE_LENGTH,
                normalization='standard'
            )
            
            if tensor is None:
                print("⚠️  Failed to convert gesture to tensor, skipped")
                return False
            
            # Validate tensor
            if not validate_tensor(tensor):
                print("⚠️  Invalid tensor produced, skipped")
                return False
            
            # Save tensor
            sample_index = len(self.collected_tensors)
            filename = f"{self.user_id}_{self.session_timestamp}_{sample_index:03d}.npy"
            filepath = self.output_dir / filename
            
            np.save(filepath, tensor)
            self.collected_tensors.append(filepath)
            
            print(f"✓ Sample {sample_index + 1}/{self.target_samples} saved: {filename}")
            print(f"  Points: {len(primary_track.points)} → Tensor: {tensor.shape}")
            print(f"  Duration: {primary_track.points[-1].timestamp - primary_track.points[0].timestamp:.3f}s")
            
            # Show tensor statistics
            print(f"  Tensor stats: mean={np.mean(tensor):.3f}, std={np.std(tensor):.3f}, "
                  f"min={np.min(tensor):.3f}, max={np.max(tensor):.3f}")
            
            return True
        
        except Exception as e:
            print(f"❌ Error processing gesture: {e}")
            return False
    
    def get_progress(self) -> tuple:
        """Get collection progress (current, target)"""
        return len(self.collected_tensors), self.target_samples
    
    def is_complete(self) -> bool:
        """Check if target samples reached"""
        return len(self.collected_tensors) >= self.target_samples
    
    def save_manifest(self):
        """Save a manifest file listing all collected samples"""
        manifest_path = self.output_dir / f"{self.user_id}_{self.session_timestamp}_manifest.txt"
        
        with open(manifest_path, 'w') as f:
            f.write(f"User ID: {self.user_id}\n")
            f.write(f"Session: {self.session_timestamp}\n")
            f.write(f"Samples: {len(self.collected_tensors)}\n")
            f.write(f"Sequence Length: {SEQUENCE_LENGTH}\n")
            f.write(f"Normalization: standard\n")
            f.write(f"\nFiles:\n")
            for filepath in self.collected_tensors:
                f.write(f"  {filepath.name}\n")
        
        print(f"\n✓ Manifest saved: {manifest_path}")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Tensor Data Collector for Deep Learning")
    parser.add_argument('--user', type=str, required=True, 
                       help='User ID or label (e.g., "alice", "bob")')
    parser.add_argument('--device', default=None, 
                       help='Input device (auto-detects if not specified)')
    parser.add_argument('--samples', type=int, default=50, 
                       help='Number of samples to collect (default: 50)')
    parser.add_argument('--output', default='data/raw', 
                       help='Output directory (default: data/raw)')
    args = parser.parse_args()
    
    # Validate user ID (alphanumeric and underscore only)
    if not args.user.replace('_', '').isalnum():
        print("❌ Invalid user ID. Use only letters, numbers, and underscores.")
        return
    
    # Create instances
    capture = TrackpadCapture(device_path=args.device)
    visualizer = GestureVisualizer(
        width=1200,
        height=800,
        title=f"Tensor Collector - User: {args.user}",
        auto_size=True
    )
    collector = TensorCollector(
        user_id=args.user,
        output_dir=args.output,
        target_samples=args.samples
    )
    
    # Callback when gesture complete
    async def on_gesture_complete(tracks):
        if collector.add_gesture(tracks):
            current, target = collector.get_progress()
            
            if collector.is_complete():
                visualizer.set_status(f"COMPLETE ({current}/{target})", (0, 255, 0))
                collector.save_manifest()
                print(f"\n{'='*60}")
                print(f"✓ Collection complete!")
                print(f"{'='*60}")
                print(f"Collected {current} samples for user '{args.user}'")
                print(f"Files saved to: {collector.output_dir}")
                print(f"\nNext steps:")
                print(f"  1. Collect data for other users")
                print(f"  2. Train Siamese Network with collected tensors")
                print(f"  3. Use trained model for authentication")
            else:
                remaining = target - current
                visualizer.set_status(f"COLLECTING ({remaining} more)", (255, 165, 0))
        else:
            # Failed to save
            current, target = collector.get_progress()
            visualizer.set_status(f"RETRY ({current}/{target})", (255, 100, 100))
    
    # Custom UI
    def draw_custom_ui(screen, font, small_font, tiny_font):
        panel_x = screen.get_width() - 450
        panel_y = 80
        
        # Progress
        current, target = collector.get_progress()
        progress = current / target if target > 0 else 0
        
        progress_text = small_font.render(f"Progress: {current}/{target}", True, (255, 200, 0))
        screen.blit(progress_text, (panel_x, panel_y))
        
        # Progress bar
        bar_width = 400
        bar_height = 25
        pygame.draw.rect(screen, (50, 50, 50), (panel_x, panel_y + 30, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), (panel_x, panel_y + 30, int(bar_width * progress), bar_height))
        
        # Percentage
        percent_text = tiny_font.render(f"{progress * 100:.1f}%", True, (255, 255, 255))
        screen.blit(percent_text, (panel_x + bar_width // 2 - 20, panel_y + 35))
        
        # Instructions
        panel_y += 70
        lines = [
            f"User: {args.user}",
            "",
            "Draw your gesture consistently",
            "Press SPACE after each gesture",
            "",
            "What's being captured:",
            "  • Raw motion data (X, Y, Time)",
            "  • Resampled to 128 points",
            "  • Converted to deltas (dx, dy, dt)",
            "  • Normalized for neural network",
            "",
            "Output format:",
            f"  • Shape: ({SEQUENCE_LENGTH}, 3)",
            "  • Format: .npy (NumPy array)",
            f"  • Location: {collector.output_dir}",
            "",
            "Tips:",
            "  • Be consistent with your gesture",
            "  • Use the same speed and path",
            "  • Avoid very short gestures (< 0.1s)"
        ]
        
        for line in lines:
            color = (200, 200, 200) if not line.startswith("  ") else (150, 150, 150)
            inst = tiny_font.render(line, True, color)
            screen.blit(inst, (panel_x, panel_y))
            panel_y += 18
    
    visualizer.set_custom_ui_callback(draw_custom_ui)
    
    # Initial status
    visualizer.set_status(f"READY (0/{args.samples})", (128, 128, 128))
    visualizer.set_info_lines([
        f"Collecting tensors for user: {args.user}",
        "Draw your gesture and press SPACE",
        f"Target: {args.samples} samples"
    ])
    
    print(f"\nTensor Data Collector")
    print(f"=" * 60)
    print(f"User ID: {args.user}")
    print(f"Target samples: {args.samples}")
    print(f"Output directory: {collector.output_dir}")
    print(f"\nTensor format:")
    print(f"  • Shape: ({SEQUENCE_LENGTH}, 3)")
    print(f"  • Channels: [dx, dy, dt]")
    print(f"  • Normalization: Standard (zero mean, unit variance)")
    print(f"\nGesture requirements:")
    print(f"  • Minimum: 2 points")
    print(f"  • Recommended: 20+ points (0.2s+ duration)")
    print(f"  • Consistency: Try to repeat the same way")
    print(f"\nDraw your gesture {args.samples} times (press SPACE each time)")
    print(f"Files will be saved as: {args.user}_{{timestamp}}_{{index}}.npy")
    print(f"\n💡 Tip: For best results:")
    print(f"   1. Use a distinctive gesture (not too simple)")
    print(f"   2. Draw at consistent speed")
    print(f"   3. Keep the same path shape")
    
    # Run
    await run_capture_loop(capture, visualizer, on_gesture_complete)


if __name__ == "__main__":
    asyncio.run(main())
