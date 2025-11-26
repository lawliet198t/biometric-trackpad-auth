#!/usr/bin/env python3
"""
Dataset Loader for Biometric Training

Loads .npy gesture tensors and creates triplets for Siamese Network training.

Triplet Structure:
- Anchor: User A's gesture
- Positive: Another gesture from User A (same user)
- Negative: Gesture from User B or random user (different user)

The network learns to minimize distance(anchor, positive) and
maximize distance(anchor, negative).
"""

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from typing import List, Tuple, Dict
import random


class GestureTripletDataset(Dataset):
    """
    PyTorch Dataset for loading gesture triplets.
    
    Automatically scans data/raw/ directory and organizes by user ID.
    Generates (anchor, positive, negative) triplets on-the-fly.
    """
    
    def __init__(self, data_dir: str = "data/raw", 
                 min_samples_per_user: int = 10,
                 transform=None):
        """
        Initialize dataset.
        
        Args:
            data_dir: Directory containing .npy files
            min_samples_per_user: Minimum samples required per user
            transform: Optional transform to apply to tensors
        """
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.min_samples_per_user = min_samples_per_user
        
        # Load and organize data by user
        self.user_data = self._load_data()
        
        # Filter users with insufficient samples
        self.user_data = {
            user: samples for user, samples in self.user_data.items()
            if len(samples) >= min_samples_per_user
        }
        
        if len(self.user_data) < 2:
            raise ValueError(
                f"Need at least 2 users with {min_samples_per_user}+ samples. "
                f"Found {len(self.user_data)} users."
            )
        
        self.users = list(self.user_data.keys())
        
        # Calculate dataset size (number of possible triplets)
        # For each user, we can create N * (N-1) anchor-positive pairs
        # Then pair each with a random negative
        self.triplets_per_user = sum(
            len(samples) * (len(samples) - 1) 
            for samples in self.user_data.values()
        )
        
        print(f"✓ Dataset loaded:")
        print(f"  Users: {len(self.users)}")
        print(f"  Total samples: {sum(len(s) for s in self.user_data.values())}")
        print(f"  Possible triplets: {self.triplets_per_user}")
        for user, samples in self.user_data.items():
            print(f"    {user}: {len(samples)} samples")
    
    def _load_data(self) -> Dict[str, List[np.ndarray]]:
        """
        Load all .npy files and organize by user ID.
        
        File naming convention: {user_id}_{timestamp}_{index}.npy
        
        Returns:
            Dictionary mapping user_id -> list of tensors
        """
        user_data = {}
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        
        # Find all .npy files
        npy_files = list(self.data_dir.glob("*.npy"))
        
        if len(npy_files) == 0:
            raise FileNotFoundError(f"No .npy files found in {self.data_dir}")
        
        for filepath in npy_files:
            # Skip manifest files
            if "manifest" in filepath.name:
                continue
            
            # Extract user ID from filename
            # Format: {user_id}_{timestamp}_{index}.npy
            parts = filepath.stem.split('_')
            if len(parts) < 3:
                print(f"⚠️  Skipping invalid filename: {filepath.name}")
                continue
            
            user_id = parts[0]
            
            # Load tensor
            try:
                tensor = np.load(filepath)
                
                # Validate shape
                if tensor.shape != (128, 3):
                    print(f"⚠️  Invalid shape {tensor.shape} in {filepath.name}, skipping")
                    continue
                
                # Validate no NaN/Inf
                if np.any(np.isnan(tensor)) or np.any(np.isinf(tensor)):
                    print(f"⚠️  Invalid values in {filepath.name}, skipping")
                    continue
                
                # Add to user's data
                if user_id not in user_data:
                    user_data[user_id] = []
                
                user_data[user_id].append(tensor)
            
            except Exception as e:
                print(f"⚠️  Error loading {filepath.name}: {e}")
                continue
        
        return user_data
    
    def __len__(self) -> int:
        """Return dataset size (number of triplets)"""
        return self.triplets_per_user
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Get a triplet (anchor, positive, negative).
        
        Args:
            idx: Index (not actually used, we generate random triplets)
        
        Returns:
            (anchor, positive, negative) tuple of tensors
            Each tensor has shape (3, 128) - note channel-first for Conv1D
        """
        # Select random user for anchor
        anchor_user = random.choice(self.users)
        
        # Get anchor and positive from same user
        user_samples = self.user_data[anchor_user]
        
        if len(user_samples) < 2:
            # Fallback: use same sample (shouldn't happen due to filtering)
            anchor_idx = positive_idx = 0
        else:
            # Select two different samples from same user
            anchor_idx, positive_idx = random.sample(range(len(user_samples)), 2)
        
        anchor = user_samples[anchor_idx]
        positive = user_samples[positive_idx]
        
        # Get negative from different user
        negative_user = random.choice([u for u in self.users if u != anchor_user])
        negative_samples = self.user_data[negative_user]
        negative_idx = random.randint(0, len(negative_samples) - 1)
        negative = negative_samples[negative_idx]
        
        # Convert to torch tensors
        # Transpose from (128, 3) to (3, 128) for Conv1D (channel-first)
        anchor = torch.from_numpy(anchor.T).float()      # (3, 128)
        positive = torch.from_numpy(positive.T).float()  # (3, 128)
        negative = torch.from_numpy(negative.T).float()  # (3, 128)
        
        # Apply transforms if any
        if self.transform:
            anchor = self.transform(anchor)
            positive = self.transform(positive)
            negative = self.transform(negative)
        
        return anchor, positive, negative


class GesturePairDataset(Dataset):
    """
    PyTorch Dataset for loading gesture pairs (for contrastive learning).
    
    Generates (sample1, sample2, label) where:
    - label = 1 if same user (positive pair)
    - label = 0 if different users (negative pair)
    """
    
    def __init__(self, data_dir: str = "data/raw",
                 min_samples_per_user: int = 10,
                 positive_ratio: float = 0.5,
                 transform=None):
        """
        Initialize pair dataset.
        
        Args:
            data_dir: Directory containing .npy files
            min_samples_per_user: Minimum samples per user
            positive_ratio: Ratio of positive pairs (default: 0.5)
            transform: Optional transform
        """
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.positive_ratio = positive_ratio
        
        # Reuse triplet dataset's loading logic
        triplet_dataset = GestureTripletDataset(
            data_dir=data_dir,
            min_samples_per_user=min_samples_per_user
        )
        
        self.user_data = triplet_dataset.user_data
        self.users = triplet_dataset.users
        
        # Calculate dataset size
        total_samples = sum(len(samples) for samples in self.user_data.values())
        self.dataset_size = total_samples * 10  # Arbitrary multiplier
        
        print(f"✓ Pair dataset loaded:")
        print(f"  Users: {len(self.users)}")
        print(f"  Total samples: {total_samples}")
        print(f"  Positive ratio: {positive_ratio}")
    
    def __len__(self) -> int:
        return self.dataset_size
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, int]:
        """
        Get a pair (sample1, sample2, label).
        
        Returns:
            (sample1, sample2, label) where label is 0 or 1
        """
        # Decide if positive or negative pair
        is_positive = random.random() < self.positive_ratio
        
        if is_positive:
            # Same user
            user = random.choice(self.users)
            samples = self.user_data[user]
            
            if len(samples) < 2:
                idx1 = idx2 = 0
            else:
                idx1, idx2 = random.sample(range(len(samples)), 2)
            
            sample1 = samples[idx1]
            sample2 = samples[idx2]
            label = 1
        
        else:
            # Different users
            user1, user2 = random.sample(self.users, 2)
            
            samples1 = self.user_data[user1]
            samples2 = self.user_data[user2]
            
            idx1 = random.randint(0, len(samples1) - 1)
            idx2 = random.randint(0, len(samples2) - 1)
            
            sample1 = samples1[idx1]
            sample2 = samples2[idx2]
            label = 0
        
        # Convert to torch tensors (channel-first)
        sample1 = torch.from_numpy(sample1.T).float()
        sample2 = torch.from_numpy(sample2.T).float()
        
        if self.transform:
            sample1 = self.transform(sample1)
            sample2 = self.transform(sample2)
        
        return sample1, sample2, label


def create_dataloaders(data_dir: str = "data/raw",
                      batch_size: int = 32,
                      train_split: float = 0.8,
                      min_samples_per_user: int = 10,
                      num_workers: int = 4) -> Tuple[DataLoader, DataLoader]:
    """
    Create train and validation dataloaders.
    
    Args:
        data_dir: Data directory
        batch_size: Batch size
        train_split: Train/val split ratio
        min_samples_per_user: Minimum samples per user
        num_workers: Number of worker processes
    
    Returns:
        (train_loader, val_loader) tuple
    """
    # Create dataset
    dataset = GestureTripletDataset(
        data_dir=data_dir,
        min_samples_per_user=min_samples_per_user
    )
    
    # Split into train/val
    dataset_size = len(dataset)
    train_size = int(train_split * dataset_size)
    val_size = dataset_size - train_size
    
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size]
    )
    
    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    print(f"\n✓ Dataloaders created:")
    print(f"  Train samples: {train_size}")
    print(f"  Val samples: {val_size}")
    print(f"  Batch size: {batch_size}")
    
    return train_loader, val_loader


if __name__ == "__main__":
    print("Gesture Dataset Loader Test")
    print("=" * 60)
    
    try:
        # Test dataset loading
        dataset = GestureTripletDataset(
            data_dir="data/raw",
            min_samples_per_user=5
        )
        
        print(f"\n✓ Dataset loaded successfully")
        print(f"  Total triplets: {len(dataset)}")
        
        # Test getting a sample
        anchor, positive, negative = dataset[0]
        
        print(f"\n✓ Sample triplet:")
        print(f"  Anchor shape: {anchor.shape}")
        print(f"  Positive shape: {positive.shape}")
        print(f"  Negative shape: {negative.shape}")
        
        # Test dataloader
        print(f"\n✓ Testing DataLoader...")
        train_loader, val_loader = create_dataloaders(
            data_dir="data/raw",
            batch_size=4,
            min_samples_per_user=5,
            num_workers=0  # Use 0 for testing
        )
        
        # Get one batch
        anchor_batch, positive_batch, negative_batch = next(iter(train_loader))
        
        print(f"\n✓ Batch loaded:")
        print(f"  Anchor batch: {anchor_batch.shape}")
        print(f"  Positive batch: {positive_batch.shape}")
        print(f"  Negative batch: {negative_batch.shape}")
        
        print(f"\n✓ All tests passed!")
    
    except FileNotFoundError as e:
        print(f"\n⚠️  {e}")
        print(f"\nTo test the dataset loader:")
        print(f"  1. Run: python3 collect_tensors.py --user alice --samples 20")
        print(f"  2. Run: python3 collect_tensors.py --user bob --samples 20")
        print(f"  3. Run: python3 dataset_loader.py")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
