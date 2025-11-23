#!/usr/bin/env python3
"""
Tensor Processor for Deep Learning Pipeline

Transforms variable-length gesture data into fixed-length tensors suitable for
Siamese Network training. This module handles:
- Sequence resampling to fixed length (128 points)
- Delta computation (relative movements)
- Normalization for neural network input

Hardware Constraint: Works with (X, Y, Timestamp) data only
Output: Fixed-size (128, 3) numpy arrays ready for AI training
"""

import numpy as np
from typing import List, Tuple
from dataclasses import dataclass


# Fixed sequence length for all gestures
SEQUENCE_LENGTH = 128


@dataclass
class TouchPoint:
    """Single touch point with position and timing"""
    x: float
    y: float
    timestamp: float
    timestamp_ns: int


class TensorProcessor:
    """
    Process variable-length gesture data into fixed-length tensors.
    
    Pipeline:
    1. Resample to fixed length (128 points) using linear interpolation
    2. Compute deltas (relative movements: dx, dy, dt)
    3. Normalize for neural network input
    
    Output shape: (128, 3) where channels are [dx, dy, dt]
    """
    
    def __init__(self, sequence_length: int = SEQUENCE_LENGTH, 
                 normalization: str = 'standard'):
        """
        Initialize tensor processor.
        
        Args:
            sequence_length: Fixed output sequence length (default: 128)
            normalization: Normalization method ('standard' or 'minmax')
        """
        self.sequence_length = sequence_length
        self.normalization = normalization
        
        if normalization not in ['standard', 'minmax']:
            raise ValueError(f"Invalid normalization: {normalization}. Use 'standard' or 'minmax'")
    
    def resample_sequence(self, points: List[TouchPoint]) -> np.ndarray:
        """
        Resample variable-length sequence to fixed length using linear interpolation.
        
        Interpolation is based on cumulative path distance to preserve speed information.
        This ensures that fast movements are represented with larger spacing between points,
        and slow movements with smaller spacing.
        
        Args:
            points: List of TouchPoint objects (variable length)
        
        Returns:
            Resampled array of shape (sequence_length, 3) with [x, y, timestamp]
        """
        if len(points) < 2:
            raise ValueError(f"Need at least 2 points to resample, got {len(points)}")
        
        # Extract coordinates and timestamps
        x_coords = np.array([p.x for p in points])
        y_coords = np.array([p.y for p in points])
        timestamps = np.array([p.timestamp for p in points])
        
        # Calculate cumulative distance along path (arc length parameterization)
        # This preserves speed information during resampling
        dx = np.diff(x_coords)
        dy = np.diff(y_coords)
        segment_distances = np.sqrt(dx**2 + dy**2)
        cumulative_distance = np.concatenate([[0], np.cumsum(segment_distances)])
        
        # Handle edge case: all points are at same location (zero distance)
        if cumulative_distance[-1] == 0:
            # Fall back to uniform time-based interpolation
            cumulative_distance = timestamps - timestamps[0]
        
        # Create uniform sampling points along the path
        total_distance = cumulative_distance[-1]
        if total_distance > 0:
            uniform_distances = np.linspace(0, total_distance, self.sequence_length)
        else:
            # Fallback: uniform indices
            uniform_distances = np.linspace(0, len(points) - 1, self.sequence_length)
            cumulative_distance = np.arange(len(points), dtype=float)
        
        # Interpolate x, y, and timestamp at uniform distances
        x_resampled = np.interp(uniform_distances, cumulative_distance, x_coords)
        y_resampled = np.interp(uniform_distances, cumulative_distance, y_coords)
        t_resampled = np.interp(uniform_distances, cumulative_distance, timestamps)
        
        # Stack into (sequence_length, 3) array
        resampled = np.stack([x_resampled, y_resampled, t_resampled], axis=1)
        
        return resampled
    
    def compute_deltas(self, points_array: np.ndarray) -> np.ndarray:
        """
        Convert absolute coordinates to relative movements (deltas).
        
        This transformation makes the gesture position-invariant and focuses on
        the motion dynamics, which are the key biometric features.
        
        Args:
            points_array: Array of shape (sequence_length, 3) with [x, y, timestamp]
        
        Returns:
            Delta array of shape (sequence_length, 3) with [dx, dy, dt]
            First row is zeros (no previous point to compare)
        """
        if points_array.shape[0] < 2:
            raise ValueError(f"Need at least 2 points to compute deltas")
        
        # Compute differences between consecutive points
        deltas = np.diff(points_array, axis=0)
        
        # Prepend zeros for first point (no previous point)
        first_row = np.zeros((1, 3))
        deltas_with_first = np.vstack([first_row, deltas])
        
        return deltas_with_first
    
    def normalize(self, tensor: np.ndarray) -> np.ndarray:
        """
        Normalize tensor for neural network input.
        
        Two methods available:
        - 'standard': Zero mean, unit variance (Z-score normalization)
        - 'minmax': Scale to [0, 1] range
        
        Args:
            tensor: Array of shape (sequence_length, 3)
        
        Returns:
            Normalized array of same shape
        """
        if self.normalization == 'standard':
            # Standard scaling: (x - mean) / std
            # Apply per-channel to preserve relative magnitudes
            mean = np.mean(tensor, axis=0, keepdims=True)
            std = np.std(tensor, axis=0, keepdims=True)
            
            # Avoid division by zero
            std = np.where(std == 0, 1.0, std)
            
            normalized = (tensor - mean) / std
        
        elif self.normalization == 'minmax':
            # MinMax scaling: (x - min) / (max - min)
            # Apply per-channel
            min_val = np.min(tensor, axis=0, keepdims=True)
            max_val = np.max(tensor, axis=0, keepdims=True)
            
            # Avoid division by zero
            range_val = max_val - min_val
            range_val = np.where(range_val == 0, 1.0, range_val)
            
            normalized = (tensor - min_val) / range_val
        
        else:
            # Should never reach here due to __init__ validation
            normalized = tensor
        
        return normalized
    
    def process(self, points: List[TouchPoint]) -> np.ndarray:
        """
        Complete processing pipeline: resample -> deltas -> normalize.
        
        Args:
            points: List of TouchPoint objects (variable length)
        
        Returns:
            Processed tensor of shape (sequence_length, 3) ready for neural network
        """
        # Validate input
        if len(points) < 2:
            raise ValueError(f"Need at least 2 points to process, got {len(points)}")
        
        # Step 1: Resample to fixed length
        resampled = self.resample_sequence(points)
        
        # Step 2: Compute deltas (relative movements)
        deltas = self.compute_deltas(resampled)
        
        # Step 3: Normalize
        normalized = self.normalize(deltas)
        
        return normalized
    
    def process_batch(self, points_list: List[List[TouchPoint]]) -> np.ndarray:
        """
        Process multiple gestures into a batch tensor.
        
        Args:
            points_list: List of gesture point lists
        
        Returns:
            Batch tensor of shape (batch_size, sequence_length, 3)
        """
        batch = []
        
        for points in points_list:
            try:
                tensor = self.process(points)
                batch.append(tensor)
            except ValueError as e:
                print(f"⚠️  Skipping invalid gesture: {e}")
                continue
        
        if len(batch) == 0:
            raise ValueError("No valid gestures in batch")
        
        return np.array(batch)


def validate_tensor(tensor: np.ndarray, expected_shape: Tuple[int, int] = (SEQUENCE_LENGTH, 3)) -> bool:
    """
    Validate that a tensor has the correct shape and no invalid values.
    
    Args:
        tensor: Tensor to validate
        expected_shape: Expected shape (default: (128, 3))
    
    Returns:
        True if valid, False otherwise
    """
    # Check shape
    if tensor.shape != expected_shape:
        print(f"❌ Invalid shape: {tensor.shape}, expected {expected_shape}")
        return False
    
    # Check for NaN or Inf
    if np.any(np.isnan(tensor)):
        print(f"❌ Tensor contains NaN values")
        return False
    
    if np.any(np.isinf(tensor)):
        print(f"❌ Tensor contains Inf values")
        return False
    
    return True


if __name__ == "__main__":
    print("Tensor Processor for Deep Learning Pipeline")
    print("=" * 60)
    print(f"Fixed sequence length: {SEQUENCE_LENGTH}")
    print(f"Output shape: ({SEQUENCE_LENGTH}, 3)")
    print(f"Channels: [dx, dy, dt]")
    print("\nFeatures:")
    print("  ✓ Arc-length based resampling (preserves speed)")
    print("  ✓ Delta computation (position-invariant)")
    print("  ✓ Standard/MinMax normalization")
    print("  ✓ Batch processing support")
    print("\nImport this module to use in your data pipeline.")
