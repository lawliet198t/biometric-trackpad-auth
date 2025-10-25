#!/usr/bin/env python3
"""
Quick test of the simple Windows touchpad implementation
"""

import time
import sys

def test_simple_reader():
    """Test SimpleTouchpadReader directly"""
    print("Testing SimpleTouchpadReader...")
    print("-" * 60)
    
    try:
        from simple_windows_touchpad import SimpleTouchpadReader
        
        reader = SimpleTouchpadReader()
        
        if not reader.start():
            print("✗ Failed to start reader")
            return False
        
        print("✓ Reader started")
        print("\nTouch your touchpad for 3 seconds...")
        
        start_time = time.time()
        contact_count = 0
        
        while time.time() - start_time < 3.0:
            contacts = reader.read_contacts()
            
            if contacts:
                contact_count += 1
                print(f"  {len(contacts)} contact(s): ", end="")
                for c in contacts:
                    print(f"[{c['ContactId']}: {c['X']:.1f}, {c['Y']:.1f}] ", end="")
                print()
            
            time.sleep(0.016)
        
        reader.stop()
        
        if contact_count > 0:
            print(f"\n✓ Received {contact_count} contact updates")
            return True
        else:
            print("\n⚠️  No contacts detected (did you touch the touchpad?)")
            return False
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trackpad_lib():
    """Test trackpad_lib integration"""
    print("\n\nTesting trackpad_lib integration...")
    print("-" * 60)
    
    try:
        from trackpad_lib import detect_trackpad, list_all_trackpads
        
        # Test detection
        result = detect_trackpad()
        print(f"detect_trackpad(): {result}")
        
        # Test listing
        devices = list_all_trackpads()
        print(f"\nAvailable devices: {len(devices)}")
        for dev in devices:
            print(f"  - {dev['name']}")
        
        if result:
            print("\n✓ trackpad_lib integration working")
            return True
        else:
            print("\n⚠️  No touchpad detected")
            return False
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*60)
    print("Simple Windows Touchpad Test")
    print("="*60)
    print()
    
    # Test 1: Direct reader
    test1 = test_simple_reader()
    
    # Test 2: trackpad_lib integration
    test2 = test_trackpad_lib()
    
    print("\n" + "="*60)
    print("Results:")
    print(f"  SimpleTouchpadReader: {'✓ PASS' if test1 else '✗ FAIL'}")
    print(f"  trackpad_lib:         {'✓ PASS' if test2 else '✗ FAIL'}")
    print("="*60)
    
    sys.exit(0 if (test1 and test2) else 1)
