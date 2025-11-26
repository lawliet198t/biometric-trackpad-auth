#!/usr/bin/env python3
"""
AI Training Script for Biometric Authentication

Trains a Siamese Network using Triplet Loss on gesture data.

Workflow:
1. Load .npy files from data/raw/
2. Create triplets (anchor, positive, negative)
3. Train network to minimize distance(anchor, positive)
   and maximize distance(anchor, negative)
4. Save best model to model.pth

Usage:
    python3 train_ai.py --epochs 100 --batch-size 32
    python3 train_ai.py --data data/raw --model-output models/touchid.pth
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import argparse
from pathlib import Path
import time
import json

from biometric_model import SiameseNetwork, TouchIDNet
from dataset_loader import GestureTripletDataset, create_dataloaders


class TripletLoss(nn.Module):
    """
    Triplet Loss for Siamese Networks.
    
    Loss = max(0, distance(anchor, positive) - distance(anchor, negative) + margin)
    
    The network learns to:
    - Pull anchor and positive closer (minimize distance)
    - Push anchor and negative apart (maximize distance)
    - Maintain at least 'margin' separation
    """
    
    def __init__(self, margin: float = 1.0):
        """
        Initialize Triplet Loss.
        
        Args:
            margin: Minimum separation between positive and negative (default: 1.0)
        """
        super(TripletLoss, self).__init__()
        self.margin = margin
    
    def forward(self, anchor, positive, negative):
        """
        Compute triplet loss.
        
        Args:
            anchor: Anchor embeddings (batch, embedding_dim)
            positive: Positive embeddings (batch, embedding_dim)
            negative: Negative embeddings (batch, embedding_dim)
        
        Returns:
            Loss value (scalar)
        """
        # Euclidean distance
        distance_positive = torch.norm(anchor - positive, p=2, dim=1)
        distance_negative = torch.norm(anchor - negative, p=2, dim=1)
        
        # Triplet loss
        losses = torch.relu(distance_positive - distance_negative + self.margin)
        
        return losses.mean()


class Trainer:
    """
    Training manager for Siamese Network.
    """
    
    def __init__(self, model, train_loader, val_loader, 
                 device='cuda', learning_rate=0.001, margin=1.0):
        """
        Initialize trainer.
        
        Args:
            model: SiameseNetwork model
            train_loader: Training data loader
            val_loader: Validation data loader
            device: 'cuda' or 'cpu'
            learning_rate: Learning rate
            margin: Triplet loss margin
        """
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.device = device
        
        # Loss and optimizer
        self.criterion = TripletLoss(margin=margin)
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        
        # Learning rate scheduler (reduce on plateau)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=5, verbose=True
        )
        
        # Training history
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'learning_rate': []
        }
        
        self.best_val_loss = float('inf')
        self.best_model_state = None
    
    def train_epoch(self):
        """Train for one epoch."""
        self.model.train()
        total_loss = 0.0
        num_batches = 0
        
        for batch_idx, (anchor, positive, negative) in enumerate(self.train_loader):
            # Move to device
            anchor = anchor.to(self.device)
            positive = positive.to(self.device)
            negative = negative.to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            emb_anchor, emb_positive, emb_negative = self.model(anchor, positive, negative)
            
            # Compute loss
            loss = self.criterion(emb_anchor, emb_positive, emb_negative)
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
            
            # Print progress every 10 batches
            if (batch_idx + 1) % 10 == 0:
                avg_loss = total_loss / num_batches
                print(f"  Batch {batch_idx + 1}/{len(self.train_loader)}: Loss = {avg_loss:.4f}")
        
        return total_loss / num_batches
    
    def validate(self):
        """Validate on validation set."""
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for anchor, positive, negative in self.val_loader:
                # Move to device
                anchor = anchor.to(self.device)
                positive = positive.to(self.device)
                negative = negative.to(self.device)
                
                # Forward pass
                emb_anchor, emb_positive, emb_negative = self.model(anchor, positive, negative)
                
                # Compute loss
                loss = self.criterion(emb_anchor, emb_positive, emb_negative)
                
                total_loss += loss.item()
                num_batches += 1
        
        return total_loss / num_batches
    
    def train(self, num_epochs: int, save_path: str = "model.pth"):
        """
        Train for multiple epochs.
        
        Args:
            num_epochs: Number of epochs
            save_path: Path to save best model
        """
        print(f"\n{'='*60}")
        print(f"Starting Training")
        print(f"{'='*60}")
        print(f"Device: {self.device}")
        print(f"Epochs: {num_epochs}")
        print(f"Learning rate: {self.optimizer.param_groups[0]['lr']}")
        print(f"Triplet margin: {self.criterion.margin}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        for epoch in range(num_epochs):
            epoch_start = time.time()
            
            print(f"Epoch {epoch + 1}/{num_epochs}")
            print("-" * 60)
            
            # Train
            train_loss = self.train_epoch()
            
            # Validate
            val_loss = self.validate()
            
            # Update learning rate
            self.scheduler.step(val_loss)
            current_lr = self.optimizer.param_groups[0]['lr']
            
            # Save history
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['learning_rate'].append(current_lr)
            
            # Save best model
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.best_model_state = self.model.state_dict().copy()
                
                # Save to disk
                torch.save({
                    'epoch': epoch + 1,
                    'model_state_dict': self.best_model_state,
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'train_loss': train_loss,
                    'val_loss': val_loss,
                    'history': self.history
                }, save_path)
                
                print(f"  ✓ Best model saved (val_loss: {val_loss:.4f})")
            
            epoch_time = time.time() - epoch_start
            
            print(f"  Train Loss: {train_loss:.4f}")
            print(f"  Val Loss:   {val_loss:.4f}")
            print(f"  LR:         {current_lr:.6f}")
            print(f"  Time:       {epoch_time:.1f}s")
            print()
        
        total_time = time.time() - start_time
        
        print(f"{'='*60}")
        print(f"Training Complete!")
        print(f"{'='*60}")
        print(f"Total time: {total_time/60:.1f} minutes")
        print(f"Best val loss: {self.best_val_loss:.4f}")
        print(f"Model saved to: {save_path}")
        print(f"{'='*60}\n")
        
        # Save training history
        history_path = Path(save_path).parent / "training_history.json"
        with open(history_path, 'w') as f:
            json.dump(self.history, f, indent=2)
        print(f"Training history saved to: {history_path}")


def main():
    parser = argparse.ArgumentParser(description="Train Biometric Siamese Network")
    
    # Data arguments
    parser.add_argument('--data', type=str, default='data/raw',
                       help='Data directory (default: data/raw)')
    parser.add_argument('--min-samples', type=int, default=10,
                       help='Minimum samples per user (default: 10)')
    
    # Training arguments
    parser.add_argument('--epochs', type=int, default=100,
                       help='Number of epochs (default: 100)')
    parser.add_argument('--batch-size', type=int, default=32,
                       help='Batch size (default: 32)')
    parser.add_argument('--lr', type=float, default=0.001,
                       help='Learning rate (default: 0.001)')
    parser.add_argument('--margin', type=float, default=1.0,
                       help='Triplet loss margin (default: 1.0)')
    
    # Model arguments
    parser.add_argument('--embedding-dim', type=int, default=128,
                       help='Embedding dimension (default: 128)')
    parser.add_argument('--dropout', type=float, default=0.3,
                       help='Dropout rate (default: 0.3)')
    
    # Output arguments
    parser.add_argument('--model-output', type=str, default='model.pth',
                       help='Model save path (default: model.pth)')
    
    # Device arguments
    parser.add_argument('--device', type=str, default='auto',
                       help='Device: cuda, cpu, or auto (default: auto)')
    parser.add_argument('--num-workers', type=int, default=4,
                       help='DataLoader workers (default: 4)')
    
    args = parser.parse_args()
    
    # Determine device
    if args.device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    else:
        device = args.device
    
    print(f"Biometric AI Training")
    print(f"=" * 60)
    print(f"Configuration:")
    print(f"  Data directory: {args.data}")
    print(f"  Min samples per user: {args.min_samples}")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Learning rate: {args.lr}")
    print(f"  Triplet margin: {args.margin}")
    print(f"  Embedding dim: {args.embedding_dim}")
    print(f"  Dropout: {args.dropout}")
    print(f"  Device: {device}")
    print(f"  Model output: {args.model_output}")
    print(f"=" * 60)
    
    # Create output directory
    output_path = Path(args.model_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print(f"\nLoading data...")
    try:
        train_loader, val_loader = create_dataloaders(
            data_dir=args.data,
            batch_size=args.batch_size,
            min_samples_per_user=args.min_samples,
            num_workers=args.num_workers
        )
    except Exception as e:
        print(f"\n❌ Error loading data: {e}")
        print(f"\nMake sure you have collected training data:")
        print(f"  python3 collect_tensors.py --user alice --samples 30")
        print(f"  python3 collect_tensors.py --user bob --samples 30")
        return
    
    # Create model
    print(f"\nCreating model...")
    model = SiameseNetwork(
        embedding_dim=args.embedding_dim,
        dropout=args.dropout
    )
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Total parameters: {total_params:,}")
    
    # Create trainer
    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        device=device,
        learning_rate=args.lr,
        margin=args.margin
    )
    
    # Train
    trainer.train(num_epochs=args.epochs, save_path=args.model_output)
    
    print(f"\n✓ Training complete!")
    print(f"\nNext steps:")
    print(f"  1. Test the model: python3 ai_verifier.py --model {args.model_output}")
    print(f"  2. Collect more data to improve accuracy")
    print(f"  3. Tune hyperparameters (learning rate, margin, etc.)")


if __name__ == "__main__":
    main()
