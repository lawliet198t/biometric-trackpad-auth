#!/usr/bin/env python3
"""
Linux Touchpad Dimension Test

This script specifically tests Linux touchpad dimension detection
and window adaptation.
"""

import asyncio
import time
import platform
from trackpad_lib import (
    TrackpadCapture, GestureVisualizer, 
    calculate_window_size_from_touchpad,
    detect_trackpad, list_all_trackpads
)


async def main():
    print("="*70)
    print("Linux Touchpad Dimension Test")
    print("="*70)
    print()
    
    # Check platform
    if platform.system() != 'Linux':
        print("❌ This test is for Linux only!")
        print(f"   Current platform: {platform.system()}")
        print()
        print("For Windows, use: python3 test_dimension_fix.py")
        return
    
    print("✓ Linux platform detected")
    print()
    
    # List all available touchpads
    print("="*70)
    print("Step 1: Detecting Available Touchpads")
    print("="*70)
    print()
    
    touchpads = list_all_trackpads()
    
    if not touchpads:
        print("❌ No touchpads detected!")
        print()
        print("Troubleshooting:")
        print("  1. Make sure evdev is installed: pip install evdev")
        print("  2. Check if touchpad is working: cat /proc/bus/input/devices")
        print("  3. You may need to run with sudo for device access")
        return
    
    print(f"✓ Found {len(touchpads)} touchpad device(s):")
    print()
    for i, tp in enumerate(touchpads, 1):
        print(f"  {i}. {tp['path']}")
        print(f"     Name: {tp['name']}")
        print(f"     Score: {tp['score']}")
        if tp.get('is_trackpad_name'):
            print(f"     ✓ Confirmed trackpad (name match)")
        print()
    
    # Auto-detect best touchpad
    print("="*70)
    print("Step 2: Auto-Detecting Best Touchpad")
    print("="*70)
    print()
    
    best_device = detect_trackpad()
    if best_device:
        print(f"✓ Auto-detected: {best_device}")
    else:
        print("❌ Auto-detection failed")
        return
    
    print()
    
    # Create capture instance
    print("="*70)
    print("Step 3: Reading Device Capabilities")
    print("="*70)
    print()
    
    try:
        capture = TrackpadCapture(device_path=best_device)
    except Exception as e:
        print(f"❌ Failed to create capture: {e}")
        print()
        print("You may need to run with sudo:")
        print(f"  sudo python3 {__file__}")
        return
    
    # Open device
    if not capture.open_device():
        print("❌ Failed to open device")
        print()
        print("You may need to run with sudo:")
        print(f"  sudo python3 {__file__}")
        return
    
    print("✓ Device opened successfully")
    print()
    
    # Display device capabilities
    print("Device Capabilities:")
    print(f"  Device: {capture.device.name}")
    print(f"  Path: {capture.device_path}")
    print()
    
    print("Coordinate Ranges:")
    print(f"  X: {capture.abs_x_min} to {capture.abs_x_max}")
    print(f"  Y: {capture.abs_y_min} to {capture.abs_y_max}")
    print()
    
    # Get dimensions
    print("="*70)
    print("Step 4: Calculating Touchpad Dimensions")
    print("="*70)
    print()
    
    width, height = capture.get_touchpad_dimensions()
    aspect_ratio = width / height if height > 0 else 1.0
    
    print("Touchpad Dimensions:")
    print(f"  Width:  {width:6d} units")
    print(f"  Height: {height:6d} units")
    print(f"  Aspect Ratio: {aspect_ratio:.2f}:1")
    print()
    
    # Validate dimensions
    if width <= 0 or height <= 0:
        print("❌ Invalid dimensions detected!")
        return
    
    if width == height:
        print("⚠️  Warning: Square aspect ratio (unusual for touchpads)")
    elif 1.3 <= aspect_ratio <= 1.8:
        print("✓ Aspect ratio looks good (typical touchpad range)")
    else:
        print(f"⚠️  Warning: Unusual aspect ratio ({aspect_ratio:.2f})")
    
    print()
    
    # Calculate window size
    print("="*70)
    print("Step 5: Calculating Window Size")
    print("="*70)
    print()
    
    win_width, win_height = calculate_window_size_from_touchpad(width, height)
    win_aspect = win_width / win_height
    
    print("Recommended Window Size:")
    print(f"  Width:  {win_width:4d} pixels")
    print(f"  Height: {win_height:4d} pixels")
    print(f"  Aspect Ratio: {win_aspect:.2f}:1")
    print()
    
    # Check aspect ratio match
    aspect_diff = abs(aspect_ratio - win_aspect) / aspect_ratio * 100
    print(f"Aspect Ratio Match: {100 - aspect_diff:.1f}%")
    
    if aspect_diff < 5:
        print("✓ Excellent match!")
    elif aspect_diff < 10:
        print("✓ Good match")
    else:
        print("⚠️  Aspect ratios don't match well")
    
    print()
    
    # Test visualizer adaptation
    print("="*70)
    print("Step 6: Testing Visualizer Adaptation")
    print("="*70)
    print()
    
    visualizer = GestureVisualizer(auto_size=True)
    print(f"Initial visualizer size: {visualizer.width}x{visualizer.height}")
    
    visualizer.adapt_to_touchpad(width, height)
    print(f"Adapted visualizer size: {visualizer.width}x{visualizer.height}")
    print()
    
    if visualizer.width == win_width and visualizer.height == win_height:
        print("✓ Visualizer adapted correctly!")
    else:
        print("⚠️  Visualizer adaptation mismatch")
        print(f"   Expected: {win_width}x{win_height}")
        print(f"   Got: {visualizer.width}x{visualizer.height}")
    
    print()
    
    # Test coordinate normalization
    print("="*70)
    print("Step 7: Testing Coordinate Normalization")
    print("="*70)
    print()
    
    capture.screen_width = win_width
    capture.screen_height = win_height
    
    # Test corner coordinates
    test_coords = [
        (capture.abs_x_min, capture.abs_y_min, "Top-Left"),
        (capture.abs_x_max, capture.abs_y_min, "Top-Right"),
        (capture.abs_x_min, capture.abs_y_max, "Bottom-Left"),
        (capture.abs_x_max, capture.abs_y_max, "Bottom-Right"),
        ((capture.abs_x_min + capture.abs_x_max) // 2, 
         (capture.abs_y_min + capture.abs_y_max) // 2, "Center"),
    ]
    
    print("Testing corner and center coordinates:")
    print()
    all_in_bounds = True
    
    for raw_x, raw_y, label in test_coords:
        screen_x, screen_y = capture.normalize_coords(raw_x, raw_y)
        in_bounds = (0 <= screen_x <= win_width and 0 <= screen_y <= win_height)
        status = "✓" if in_bounds else "✗"
        
        print(f"  {status} {label:12s}: ({raw_x:6d}, {raw_y:6d}) -> ({screen_x:6.1f}, {screen_y:6.1f})")
        
        if not in_bounds:
            all_in_bounds = False
    
    print()
    if all_in_bounds:
        print("✓ All coordinates normalized correctly!")
    else:
        print("❌ Some coordinates out of bounds!")
    
    print()
    
    # Summary
    print("="*70)
    print("Test Summary")
    print("="*70)
    print()
    
    checks = [
        ("Touchpad Detection", touchpads is not None and len(touchpads) > 0),
        ("Device Opening", capture.device is not None),
        ("Dimension Reading", width > 0 and height > 0),
        ("Aspect Ratio Valid", 1.0 <= aspect_ratio <= 2.5),
        ("Window Size Calculation", win_width > 0 and win_height > 0),
        ("Aspect Ratio Match", aspect_diff < 10),
        ("Visualizer Adaptation", visualizer.width == win_width),
        ("Coordinate Normalization", all_in_bounds),
    ]
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
    
    print()
    print(f"Results: {passed}/{total} checks passed")
    print()
    
    if passed == total:
        print("="*70)
        print("🎉 ALL TESTS PASSED!")
        print("="*70)
        print()
        print("Your Linux touchpad dimension detection is working perfectly!")
        print()
        print("Next steps:")
        print("  1. Test with realtime_trainer.py")
        print("  2. Verify window matches touchpad shape")
        print("  3. Check that gestures draw smoothly")
    else:
        print("="*70)
        print("⚠️  SOME TESTS FAILED")
        print("="*70)
        print()
        print("Troubleshooting:")
        print("  1. Make sure you have proper device permissions")
        print("  2. Try running with sudo if needed")
        print("  3. Check that evdev is installed: pip install evdev")
        print("  4. Verify touchpad works in other apps")
    
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
