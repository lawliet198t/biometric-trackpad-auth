#!/usr/bin/env python3
"""
Test Touchpad Dimension Detection

This script tests the automatic touchpad dimension detection
and shows how the window adapts to match the touchpad's aspect ratio.
"""

import time
from simple_windows_touchpad import SimpleTouchpadReader


def main():
    print("="*60)
    print("Touchpad Dimension Detection Test")
    print("="*60)
    print()
    
    # Create reader
    reader = SimpleTouchpadReader()
    
    # Start reading
    if not reader.start():
        print("❌ Failed to start touchpad reader")
        return
    
    print("✓ Touchpad reader started")
    print()
    print("Touch your touchpad with multiple fingers...")
    print("Move around to help detect the full coordinate range")
    print("(Will auto-detect for 5 seconds)")
    print()
    
    # Collect data for 5 seconds
    start_time = time.time()
    sample_count = 0
    
    try:
        while time.time() - start_time < 5.0:
            contacts = reader.read_contacts()
            
            if contacts is not None and len(contacts) > 0:
                sample_count += 1
                if sample_count % 100 == 0:  # Print every 100 samples
                    ranges = reader.get_coordinate_ranges()
                    print(f"[{sample_count:4d}] X: {ranges['min_x']:5d}-{ranges['max_x']:5d}  "
                          f"Y: {ranges['min_y']:5d}-{ranges['max_y']:5d}")
            
            time.sleep(0.001)  # 1ms polling
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    finally:
        reader.stop()
    
    # Show final results
    print()
    print("="*60)
    print("Detection Complete!")
    print("="*60)
    
    ranges = reader.get_coordinate_ranges()
    reader.mark_range_detected()
    
    print()
    print(f"Samples collected: {sample_count}")
    print()
    print("Detected Touchpad Dimensions:")
    print(f"  Width:  {ranges['width']:5d} units")
    print(f"  Height: {ranges['height']:5d} units")
    print(f"  Aspect Ratio: {ranges['width']/ranges['height']:.2f}:1")
    print()
    
    # Calculate recommended window size
    from trackpad_lib import calculate_window_size_from_touchpad
    
    window_width, window_height = calculate_window_size_from_touchpad(
        ranges['width'], ranges['height']
    )
    
    print("Recommended Window Size:")
    print(f"  {window_width} x {window_height} pixels")
    print(f"  Aspect Ratio: {window_width/window_height:.2f}:1")
    print()
    print("✓ This window size will match your touchpad's proportions!")
    print()
    print("The visualization programs (realtime_trainer.py, realtime_verify.py)")
    print("will automatically use this optimal window size.")


if __name__ == "__main__":
    main()
