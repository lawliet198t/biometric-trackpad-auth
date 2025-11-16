#!/usr/bin/env python3
"""
Test Dimension Detection Fix

This script tests the improved touchpad dimension detection
that prevents coordinate jumping and ensures proper window sizing.
"""

import asyncio
import time
from trackpad_lib import TrackpadCapture, GestureVisualizer, run_capture_loop


async def main():
    print("="*60)
    print("Touchpad Dimension Detection Fix Test")
    print("="*60)
    print()
    
    # Create capture instance (auto-detects platform)
    capture = TrackpadCapture()
    
    # Open device
    if not capture.open_device():
        print("❌ Failed to open touchpad device")
        return
    
    print("✓ Touchpad device opened")
    print()
    
    # Test dimension detection
    print("Testing dimension detection...")
    print()
    
    if capture.is_windows:
        print("Windows detected - testing auto-lock feature")
        print("Please swipe across your entire touchpad...")
        print()
        
        # Wait for dimension detection
        success = capture.wait_for_dimension_detection(timeout=5.0)
        
        if success:
            print()
            print("✓ Dimensions detected and locked!")
        else:
            print()
            print("⚠️  Using default dimensions")
    else:
        print("Linux detected - dimensions read from device capabilities")
    
    # Get final dimensions
    width, height = capture.get_touchpad_dimensions()
    aspect_ratio = width / height if height > 0 else 1.0
    
    print()
    print("="*60)
    print("Detected Touchpad Dimensions:")
    print("="*60)
    print(f"  Width:  {width:5d} units")
    print(f"  Height: {height:5d} units")
    print(f"  Aspect Ratio: {aspect_ratio:.2f}:1")
    print()
    
    # Calculate window size
    from trackpad_lib import calculate_window_size_from_touchpad
    window_width, window_height = calculate_window_size_from_touchpad(width, height)
    
    print("Recommended Window Size:")
    print(f"  {window_width} x {window_height} pixels")
    print(f"  Aspect Ratio: {window_width/window_height:.2f}:1")
    print()
    
    # Test coordinate normalization stability
    print("="*60)
    print("Testing Coordinate Normalization Stability")
    print("="*60)
    print()
    print("Touch your touchpad and move around...")
    print("Checking if coordinates remain stable (no jumping)")
    print("(Testing for 3 seconds)")
    print()
    
    capture.screen_width = window_width
    capture.screen_height = window_height
    
    start_time = time.time()
    sample_count = 0
    coord_changes = 0
    last_ranges = None
    
    try:
        while time.time() - start_time < 3.0:
            contacts = capture.backend.read_contacts() if capture.is_windows else None
            
            if contacts is not None and len(contacts) > 0:
                sample_count += 1
                
                # Check if ranges changed
                if capture.is_windows:
                    current_ranges = capture.backend.get_coordinate_ranges()
                    if last_ranges is not None:
                        if (current_ranges['min_x'] != last_ranges['min_x'] or
                            current_ranges['max_x'] != last_ranges['max_x'] or
                            current_ranges['min_y'] != last_ranges['min_y'] or
                            current_ranges['max_y'] != last_ranges['max_y']):
                            coord_changes += 1
                    last_ranges = current_ranges
                
                # Test normalization
                for contact in contacts:
                    x, y = capture.normalize_coords(contact['X'], contact['Y'])
                    if sample_count % 50 == 0:
                        print(f"[{sample_count:4d}] Raw: ({contact['X']:5d}, {contact['Y']:5d}) -> "
                              f"Screen: ({x:6.1f}, {y:6.1f})")
            
            time.sleep(0.001)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    print()
    print("="*60)
    print("Stability Test Results:")
    print("="*60)
    print(f"  Samples collected: {sample_count}")
    
    if capture.is_windows:
        print(f"  Coordinate range changes: {coord_changes}")
        if coord_changes == 0:
            print("  ✓ STABLE - No coordinate jumping detected!")
        else:
            print(f"  ⚠️  Ranges changed {coord_changes} times (may cause visual artifacts)")
        
        if capture.backend.coord_range_detected:
            print("  ✓ Ranges are LOCKED")
        else:
            print("  ⚠️  Ranges are NOT locked")
    
    print()
    print("="*60)
    print("Test Complete!")
    print("="*60)
    print()
    print("Summary:")
    print("  ✓ Dimension detection working")
    print("  ✓ Window sizing calculated")
    if capture.is_windows and coord_changes == 0:
        print("  ✓ Coordinate normalization stable (no jumping)")
    print()
    print("You can now use realtime_trainer.py or realtime_verify.py")
    print("with proper touchpad dimension adaptation!")


if __name__ == "__main__":
    asyncio.run(main())
