#!/usr/bin/env python3
"""
Simplified test for tensor_processor.py only (no pygame dependency)
"""

import numpy as np
from tensor_processor import TensorProcessor, TouchPoint, validate_tensor, SEQUENCE_LENGTH


def create_synthetic_gesture(num_points: int = 50) -> list:
    """Create a synthetic gesture for testing"""
    points = []
    
    # Create a circular gesture
    for i in range(num_points):
        t = i / num_points * 2 * np.pi
        x = 500 + 200 * np.cos(t)
        y = 400 + 200 * np.sin(t)
        timestamp = i * 0.01  # 10ms between points
        timestamp_ns = int(timestamp * 1e9)
        
        points.append(TouchPoint(x, y, timestamp, timestamp_ns))
    
    return points


def test_tensor_processor():
    """Test TensorProcessor directly"""
    print("Test 1: TensorProcessor Direct Usage")
    print("=" * 60)
    
    # Create synthetic gesture
    points = create_synthetic_gesture(num_points=50)
    print(f"✓ Created synthetic gesture with {len(points)} points")
    
    # Create processor
    processor = TensorProcessor(sequence_length=SEQUENCE_LENGTH, normalization='standard')
    print(f"✓ Created TensorProcessor (length={SEQUENCE_LENGTH}, norm=standard)")
    
    # Process gesture
    tensor = processor.process(points)
    print(f"✓ Processed gesture → tensor shape: {tensor.shape}")
    
    # Validate
    is_valid = validate_tensor(tensor)
    print(f"✓ Validation: {'PASS' if is_valid else 'FAIL'}")
    
    # Show statistics
    print(f"\nTensor statistics:")
    print(f"  Mean: {np.mean(tensor):.6f}")
    print(f"  Std:  {np.std(tensor):.6f}")
    print(f"  Min:  {np.min(tensor):.6f}")
    print(f"  Max:  {np.max(tensor):.6f}")
    
    # Show first few deltas
    print(f"\nFirst 5 deltas [dx, dy, dt]:")
    for i in range(min(5, len(tensor))):
        print(f"  [{i}] dx={tensor[i,0]:8.4f}, dy={tensor[i,1]:8.4f}, dt={tensor[i,2]:8.4f}")
    
    return tensor


def test_edge_cases():
    """Test edge cases"""
    print("\n\nTest 2: Edge Cases")
    print("=" * 60)
    
    processor = TensorProcessor(sequence_length=SEQUENCE_LENGTH, normalization='standard')
    
    # Test 1: Minimum points (2)
    print("\n2.1: Minimum points (2)")
    points = create_synthetic_gesture(num_points=2)
    try:
        tensor = processor.process(points)
        print(f"  ✓ Processed 2 points → {tensor.shape}")
    except ValueError as e:
        print(f"  ❌ Error: {e}")
    
    # Test 2: Many points (1000)
    print("\n2.2: Many points (1000)")
    points = create_synthetic_gesture(num_points=1000)
    try:
        tensor = processor.process(points)
        print(f"  ✓ Processed 1000 points → {tensor.shape}")
    except ValueError as e:
        print(f"  ❌ Error: {e}")
    
    # Test 3: Very short gesture (same location)
    print("\n2.3: Stationary gesture (all same location)")
    points = [TouchPoint(100, 100, i * 0.01, int(i * 0.01 * 1e9)) for i in range(10)]
    try:
        tensor = processor.process(points)
        print(f"  ✓ Processed stationary gesture → {tensor.shape}")
        print(f"     All deltas should be near zero: max={np.max(np.abs(tensor)):.6f}")
    except ValueError as e:
        print(f"  ❌ Error: {e}")


def test_normalization_methods():
    """Test different normalization methods"""
    print("\n\nTest 3: Normalization Methods")
    print("=" * 60)
    
    points = create_synthetic_gesture(num_points=50)
    
    # Standard normalization
    print("\n3.1: Standard normalization (zero mean, unit variance)")
    processor_std = TensorProcessor(sequence_length=SEQUENCE_LENGTH, normalization='standard')
    tensor_std = processor_std.process(points)
    print(f"  Mean: {np.mean(tensor_std):.6f} (should be ~0)")
    print(f"  Std:  {np.std(tensor_std):.6f} (should be ~1)")
    
    # MinMax normalization
    print("\n3.2: MinMax normalization (0-1 range)")
    processor_minmax = TensorProcessor(sequence_length=SEQUENCE_LENGTH, normalization='minmax')
    tensor_minmax = processor_minmax.process(points)
    print(f"  Min: {np.min(tensor_minmax):.6f} (should be 0)")
    print(f"  Max: {np.max(tensor_minmax):.6f} (should be 1)")


def test_batch_processing():
    """Test batch processing"""
    print("\n\nTest 4: Batch Processing")
    print("=" * 60)
    
    processor = TensorProcessor(sequence_length=SEQUENCE_LENGTH, normalization='standard')
    
    # Create multiple gestures
    gestures = [
        create_synthetic_gesture(num_points=30),
        create_synthetic_gesture(num_points=50),
        create_synthetic_gesture(num_points=100),
    ]
    
    print(f"✓ Created {len(gestures)} synthetic gestures")
    
    # Process batch
    batch_tensor = processor.process_batch(gestures)
    print(f"✓ Processed batch → shape: {batch_tensor.shape}")
    print(f"  Expected: ({len(gestures)}, {SEQUENCE_LENGTH}, 3)")


if __name__ == "__main__":
    print("Tensor Processing Pipeline Test Suite")
    print("=" * 60)
    print()
    
    try:
        # Run tests
        test_tensor_processor()
        test_edge_cases()
        test_normalization_methods()
        test_batch_processing()
        
        print("\n\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
