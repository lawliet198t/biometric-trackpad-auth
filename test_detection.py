#!/usr/bin/env python3
"""
Cross-platform test to verify trackpad detection works
"""

import platform


def test_platform():
    """Test platform detection"""
    print("Testing platform detection...")
    try:
        system = platform.system()
        print(f"✓ Platform detected: {system}")
        
        if system not in ['Linux', 'Windows', 'Darwin']:
            print(f"⚠️  Platform '{system}' may not be fully supported")
        
        return True
    except Exception as e:
        print(f"✗ Platform detection failed: {e}")
        return False


def test_imports():
    """Test that all imports work"""
    print("\nTesting imports...")
    try:
        from trackpad_lib import detect_trackpad, list_all_trackpads, TrackpadCapture
        print("✓ Core imports successful")
        
        # Test platform-specific imports
        system = platform.system()
        if system == 'Windows':
            try:
                from windows_touchpad import WindowsTouchpadCapture
                print("✓ Windows backend imported")
            except ImportError as e:
                print(f"⚠️  Windows backend not available: {e}")
        elif system == 'Linux':
            try:
                from evdev import InputDevice
                print("✓ Linux evdev imported")
            except ImportError as e:
                print(f"⚠️  Linux evdev not available: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_detection():
    """Test trackpad detection"""
    print("\nTesting trackpad detection...")
    try:
        from trackpad_lib import detect_trackpad, list_all_trackpads
        
        # Test list_all_trackpads
        devices = list_all_trackpads()
        print(f"✓ Found {len(devices)} potential trackpad device(s)")
        
        # Test detect_trackpad
        best = detect_trackpad()
        if best:
            print(f"✓ Auto-detected: {best}")
        else:
            print("⚠️  No trackpad auto-detected (this is OK if you don't have a trackpad)")
        
        return True
    except Exception as e:
        print(f"✗ Detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trackpad_capture():
    """Test TrackpadCapture initialization"""
    print("\nTesting TrackpadCapture initialization...")
    try:
        from trackpad_lib import TrackpadCapture
        
        # Test with auto-detection (may fail if no trackpad)
        try:
            capture = TrackpadCapture()
            print(f"✓ TrackpadCapture created with auto-detection: {capture.device_path}")
        except RuntimeError as e:
            print(f"⚠️  Auto-detection failed (expected if no trackpad): {e}")
        
        # Test with manual path (won't actually open device)
        capture = TrackpadCapture(device_path="/dev/input/event99")
        print(f"✓ TrackpadCapture created with manual path: {capture.device_path}")
        
        return True
    except Exception as e:
        print(f"✗ TrackpadCapture test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("Cross-Platform Trackpad Auto-Detection Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Platform", test_platform()))
    results.append(("Imports", test_imports()))
    results.append(("Detection", test_detection()))
    results.append(("TrackpadCapture", test_trackpad_capture()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("⚠️  Some tests failed (check above for details)")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
