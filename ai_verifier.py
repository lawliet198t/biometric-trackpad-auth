#!/usr/bin/env python3
"""
AI-Based Biometric Verifier

Real-time gesture authentication using trained Siamese Network.

Replaces the old statistical verification (realtime_verify.py) with
deep learning approach.

Workflow:
1. Load trained model (model.pth)
2. Load user's template embedding
3. Capture live gesture
4. Convert to tensor
5. Compute embedding
6. Calculate similarity with template
7. Accept/Reject based on threshold

Usage:
    python3 ai_verifier.py --model model.pth --user alice
"""

import asyncio
import torch
import numpy as np
from pathlib import Path
import argparse
import json
import pygame

from trackpad_lib import TrackpadCapture, GestureVisualizer, GestureTrack, run_capture_loop
from biometric_model import SiameseNetwork, TouchIDNet, cosine_similarity
from tensor_processor import TensorProcessor


class AIVerifier:
    """
    AI-based biometric verifier using Siamese Network.
    """
    
    def __init__(self, model_path: str, threshold: float = 0.85, device='cpu'):
        """
        Initialize AI verifier.
        
        Args:
            model_path: Path to trained model (.pth file)
            threshold: Similarity threshold for acceptance (default: 0.85)
            device: 'cuda' or 'cpu'
        """
        self.model_path = Path(model_path)
        self.threshold = threshold
        self.device = device
        
        # Load model
        self.model = self._load_model()
        self.model.eval()  # Set to evaluation mode
        
        # Template embeddings (user_id -> embedding)
        self.templates = {}
        
        # Verification history
        self.verification_history = []
        
        print(f"✓ AI Verifier initialized")
        print(f"  Model: {model_path}")
        print(f"  Threshold: {threshold}")
        print(f"  Device: {device}")
    
    def _load_model(self):
        """Load trained model from checkpoint."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        # Load checkpoint
        checkpoint = torch.load(self.model_path, map_location=self.device)
        
        # Create model
        model = SiameseNetwork(embedding_dim=128, dropout=0.0)  # No dropout for inference
        
        # Load weights
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(self.device)
        
        print(f"✓ Model loaded from {self.model_path}")
        if 'epoch' in checkpoint:
            print(f"  Trained for {checkpoint['epoch']} epochs")
        if 'val_loss' in checkpoint:
            print(f"  Best val loss: {checkpoint['val_loss']:.4f}")
        
        return model
    
    def create_template(self, user_id: str, gestures: list) -> np.ndarray:
        """
        Create template embedding from multiple gestures.
        
        Args:
            user_id: User identifier
            gestures: List of GestureTrack objects
        
        Returns:
            Template embedding (averaged from multiple samples)
        """
        embeddings = []
        
        for gesture in gestures:
            # Convert to tensor
            tensor = gesture.get_tensor_representation()
            
            if tensor is None:
                print(f"⚠️  Skipping invalid gesture")
                continue
            
            # Transpose to (3, 128) for Conv1D
            tensor = torch.from_numpy(tensor.T).float().unsqueeze(0)  # (1, 3, 128)
            tensor = tensor.to(self.device)
            
            # Get embedding
            with torch.no_grad():
                embedding = self.model.get_embedding(tensor)  # (1, 128)
            
            embeddings.append(embedding.cpu().numpy())
        
        if len(embeddings) == 0:
            raise ValueError("No valid gestures for template creation")
        
        # Average embeddings
        template = np.mean(embeddings, axis=0)  # (1, 128)
        
        # Store template
        self.templates[user_id] = template
        
        print(f"✓ Template created for user '{user_id}' from {len(embeddings)} gestures")
        
        return template
    
    def save_template(self, user_id: str, filepath: str):
        """Save user template to file."""
        if user_id not in self.templates:
            raise ValueError(f"No template for user '{user_id}'")
        
        template = self.templates[user_id]
        
        # Save as .npy
        np.save(filepath, template)
        print(f"✓ Template saved to {filepath}")
    
    def load_template(self, user_id: str, filepath: str):
        """Load user template from file."""
        template = np.load(filepath)
        self.templates[user_id] = template
        print(f"✓ Template loaded for user '{user_id}' from {filepath}")
    
    def verify(self, gesture: GestureTrack, user_id: str) -> dict:
        """
        Verify a gesture against user's template.
        
        Args:
            gesture: GestureTrack object
            user_id: User to verify against
        
        Returns:
            Verification result dict with:
            - passed: bool
            - similarity: float
            - threshold: float
            - user_id: str
        """
        if user_id not in self.templates:
            raise ValueError(f"No template for user '{user_id}'. Create template first.")
        
        # Convert gesture to tensor
        tensor = gesture.get_tensor_representation()
        
        if tensor is None:
            return {
                'passed': False,
                'similarity': 0.0,
                'threshold': self.threshold,
                'user_id': user_id,
                'error': 'Invalid gesture (too short)'
            }
        
        # Transpose to (3, 128) for Conv1D
        tensor = torch.from_numpy(tensor.T).float().unsqueeze(0)  # (1, 3, 128)
        tensor = tensor.to(self.device)
        
        # Get embedding
        with torch.no_grad():
            live_embedding = self.model.get_embedding(tensor)  # (1, 128)
        
        # Get template
        template = torch.from_numpy(self.templates[user_id]).float().to(self.device)
        
        # Compute similarity
        similarity = cosine_similarity(live_embedding, template).item()
        
        # Decision
        passed = similarity >= self.threshold
        
        result = {
            'passed': passed,
            'similarity': similarity,
            'threshold': self.threshold,
            'user_id': user_id,
            'points': len(gesture.points),
            'duration': gesture.points[-1].timestamp - gesture.points[0].timestamp if len(gesture.points) > 0 else 0
        }
        
        # Save to history
        self.verification_history.append(result)
        
        return result


async def main():
    parser = argparse.ArgumentParser(description="AI-Based Biometric Verifier")
    
    # Model arguments
    parser.add_argument('--model', type=str, default='model.pth',
                       help='Path to trained model (default: model.pth)')
    parser.add_argument('--threshold', type=float, default=0.85,
                       help='Similarity threshold (default: 0.85)')
    
    # User arguments
    parser.add_argument('--user', type=str, required=True,
                       help='User ID to verify')
    parser.add_argument('--template', type=str, default=None,
                       help='Path to template file (if not provided, will create from data)')
    parser.add_argument('--create-template', action='store_true',
                       help='Create template from collected data')
    parser.add_argument('--template-samples', type=int, default=10,
                       help='Number of samples for template creation (default: 10)')
    
    # Device arguments
    parser.add_argument('--device', type=str, default='auto',
                       help='Device: cuda, cpu, or auto (default: auto)')
    parser.add_argument('--trackpad-device', default=None,
                       help='Trackpad device path (auto-detect if not specified)')
    
    args = parser.parse_args()
    
    # Determine device
    if args.device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    else:
        device = args.device
    
    print(f"AI-Based Biometric Verifier")
    print(f"=" * 60)
    print(f"User: {args.user}")
    print(f"Model: {args.model}")
    print(f"Threshold: {args.threshold}")
    print(f"Device: {device}")
    print(f"=" * 60)
    
    # Create verifier
    try:
        verifier = AIVerifier(
            model_path=args.model,
            threshold=args.threshold,
            device=device
        )
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print(f"\nTrain a model first:")
        print(f"  python3 train_ai.py --epochs 50")
        return
    
    # Load or create template
    template_path = args.template or f"templates/{args.user}_template.npy"
    
    if args.create_template or not Path(template_path).exists():
        print(f"\n📝 Creating template for user '{args.user}'...")
        print(f"   Loading samples from data/raw/...")
        
        # Load user's samples from data/raw
        data_dir = Path("data/raw")
        user_files = list(data_dir.glob(f"{args.user}_*.npy"))
        
        if len(user_files) == 0:
            print(f"\n❌ No samples found for user '{args.user}' in data/raw/")
            print(f"\nCollect samples first:")
            print(f"  python3 collect_tensors.py --user {args.user} --samples 30")
            return
        
        # Load samples (limit to template_samples)
        user_files = user_files[:args.template_samples]
        
        # Create fake GestureTracks from tensors
        from tensor_processor import TouchPoint
        gestures = []
        
        for filepath in user_files:
            tensor = np.load(filepath)
            
            # Create GestureTrack from tensor (reverse process)
            # This is a hack - in production, store raw points separately
            track = GestureTrack(finger_id=0, color=(0, 255, 0))
            
            # Reconstruct approximate points from deltas
            # Note: This loses some information, but works for template creation
            x, y, t = 0, 0, 0
            for i in range(128):
                dx, dy, dt = tensor[i]
                x += dx
                y += dy
                t += dt
                track.add_point(x, y, t, int(t * 1e9))
            
            gestures.append(track)
        
        # Create template
        verifier.create_template(args.user, gestures)
        
        # Save template
        Path(template_path).parent.mkdir(parents=True, exist_ok=True)
        verifier.save_template(args.user, template_path)
    
    else:
        print(f"\n📂 Loading template from {template_path}...")
        verifier.load_template(args.user, template_path)
    
    # Create capture and visualizer
    capture = TrackpadCapture(device_path=args.trackpad_device)
    visualizer = GestureVisualizer(
        width=1200,
        height=800,
        title=f"AI Verifier - User: {args.user}",
        auto_size=True
    )
    
    # Verification callback
    async def on_gesture_complete(tracks):
        if not tracks or len(tracks) == 0:
            return
        
        primary_track = tracks[0]
        
        # Verify
        result = verifier.verify(primary_track, args.user)
        
        # Update UI
        if result['passed']:
            visualizer.set_status(
                f"✓ AUTHENTICATED ({result['similarity']:.2%})",
                (0, 255, 0)
            )
        else:
            visualizer.set_status(
                f"✗ REJECTED ({result['similarity']:.2%})",
                (255, 0, 0)
            )
        
        # Console output
        print(f"\n{'='*60}")
        if result['passed']:
            print(f"✓ AUTHENTICATION PASSED")
        else:
            print(f"✗ AUTHENTICATION FAILED")
        print(f"{'='*60}")
        print(f"User: {result['user_id']}")
        print(f"Similarity: {result['similarity']:.4f} ({result['similarity']*100:.2f}%)")
        print(f"Threshold: {result['threshold']:.4f} ({result['threshold']*100:.2f}%)")
        print(f"Points: {result['points']}")
        print(f"Duration: {result['duration']:.3f}s")
        
        if result['passed']:
            margin = result['similarity'] - result['threshold']
            print(f"Margin: +{margin:.4f} ({margin*100:.2f}%)")
        else:
            deficit = result['threshold'] - result['similarity']
            print(f"Deficit: -{deficit:.4f} ({deficit*100:.2f}%)")
    
    # Custom UI
    def draw_custom_ui(screen, font, small_font, tiny_font):
        panel_x = screen.get_width() - 450
        panel_y = 80
        
        # User info
        user_text = small_font.render(f"User: {args.user}", True, (255, 200, 0))
        screen.blit(user_text, (panel_x, panel_y))
        panel_y += 35
        
        threshold_text = tiny_font.render(f"Threshold: {args.threshold:.2%}", True, (200, 200, 200))
        screen.blit(threshold_text, (panel_x, panel_y))
        panel_y += 25
        
        # Last verification
        if verifier.verification_history:
            last = verifier.verification_history[-1]
            
            panel_y += 10
            result_text = small_font.render(
                "Last Verification:",
                True, (100, 200, 255)
            )
            screen.blit(result_text, (panel_x, panel_y))
            panel_y += 30
            
            # Result
            passed = last['passed']
            color = (0, 255, 0) if passed else (255, 0, 0)
            status = "✓ PASS" if passed else "✗ FAIL"
            
            status_text = font.render(status, True, color)
            screen.blit(status_text, (panel_x, panel_y))
            panel_y += 50
            
            # Similarity
            sim_text = tiny_font.render(
                f"Similarity: {last['similarity']:.4f} ({last['similarity']*100:.2f}%)",
                True, color
            )
            screen.blit(sim_text, (panel_x, panel_y))
            panel_y += 20
            
            # Threshold line
            thresh_text = tiny_font.render(
                f"Threshold:  {last['threshold']:.4f} ({last['threshold']*100:.2f}%)",
                True, (200, 200, 200)
            )
            screen.blit(thresh_text, (panel_x, panel_y))
            panel_y += 20
            
            # Margin/Deficit
            if passed:
                margin = last['similarity'] - last['threshold']
                margin_text = tiny_font.render(
                    f"Margin:     +{margin:.4f} ({margin*100:.2f}%)",
                    True, (0, 255, 0)
                )
            else:
                deficit = last['threshold'] - last['similarity']
                margin_text = tiny_font.render(
                    f"Deficit:    -{deficit:.4f} ({deficit*100:.2f}%)",
                    True, (255, 100, 100)
                )
            screen.blit(margin_text, (panel_x, panel_y))
            panel_y += 30
            
            # Gesture info
            info_text = tiny_font.render(
                f"Points: {last['points']}, Duration: {last['duration']:.2f}s",
                True, (150, 150, 150)
            )
            screen.blit(info_text, (panel_x, panel_y))
        
        # Instructions
        panel_y = screen.get_height() - 200
        lines = [
            "Instructions:",
            "  1. Draw your gesture",
            "  2. Press SPACE to verify",
            "  3. Check result",
            "",
            "AI Model:",
            f"  • Siamese Network",
            f"  • Embedding: 128-dim",
            f"  • Similarity: Cosine"
        ]
        
        for line in lines:
            color = (200, 200, 200) if not line.startswith("  ") else (150, 150, 150)
            text = tiny_font.render(line, True, color)
            screen.blit(text, (panel_x, panel_y))
            panel_y += 18
    
    visualizer.set_custom_ui_callback(draw_custom_ui)
    visualizer.set_status("READY", (128, 128, 128))
    visualizer.set_info_lines([
        f"AI Verification for user: {args.user}",
        "Draw your gesture and press SPACE",
        f"Threshold: {args.threshold:.2%}"
    ])
    
    print(f"\n✓ Ready for verification")
    print(f"\nDraw your gesture and press SPACE to verify")
    print(f"Press Q or ESC to quit")
    
    # Run
    await run_capture_loop(capture, visualizer, on_gesture_complete)


if __name__ == "__main__":
    asyncio.run(main())
