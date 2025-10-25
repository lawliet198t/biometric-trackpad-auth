#!/usr/bin/env python3
"""
Test Windows HID Touchpad Multi-Touch

Tests the full HID parsing implementation for true multi-touch support.
"""

import asyncio
import time
from windows_touchpad_hid import WindowsTouchpadCaptureHID, detect_windows_touchpad

async def test_hid_multitouch():
    print("=" * 70)
    print("Windows HID Touchpad Multi-Touch Test")
    print("=" * 70)
    print()
    
    # Detect touchpad
    print("1. Detecting Precision Touchpad...")
    if detect_windows_touchpad():
        print("   ✓ Precision Touchpad detected!")
    else:
        print("   ⚠️  Not detected in registry, but will try anyway")
    print()
    
    # Create capture instance
    print("2. Initializing HID capture...")
    capture = WindowsTouchpadCaptureHID()
    
    if not capture.open_device():
        print("   ✗ Failed to initialize")
        return
    
    print()
    print("3. Starting multi-touch capture test...")
    print("   Touch your touchpad with 1-5 fingers simultaneously")
    print("   Press Ctrl+C to stop")
    print()
    
    # Start capturing
    capture.start_capture()
    
    # Callbacks
    active_fingers = set()
    
    def on_finger_down(contact_id):
        active_fingers.add(contact_id)
        print(f"   ✓ Finger {contact_id} detected (Total: {len(active_fingers)} fingers)")
    
    def on_finger_up(contact_id, points):
        if contact_id in active_fingers:
            active_fingers.remove(contact_id)
        print(f"   ✓ Finger {contact_id} lifted - {len(points)} points (Remaining: {len(active_fingers)} fingers)")
    
    # Run for 60 seconds or until Ctrl+C
    try:
        task = asyncio.create_task(
            capture.process_device_events(on_finger_down, on_finger_up)
        )
        
        start_time = time.time()
        max_fingers_seen = 0
        
        while time.time() - start_time < 60:
            await asyncio.sleep(0.1)
            
            # Track maximum fingers
            current_fingers = len(capture.active_touches)
            if current_fingers > max_fingers_seen:
                max_fingers_seen = current_fingers
                print(f"   🎉 NEW RECORD: {max_fingers_seen} fingers simultaneously!")
        
        task.cancel()
        
    except KeyboardInterrupt:
        print("\n   Stopped by user")
    
    # Summary
    capture.stop_capture()
    all_tracks = capture.get_all_tracks()
    
    print()
    print("=" * 70)
    print("Test Summary:")
    print(f"  Total gestures captured: {len(all_tracks)}")
    print(f"  Maximum simultaneous fingers: {max_fingers_seen}")
    for i, track in enumerate(all_tracks, 1):
        print(f"  Gesture {i}: {len(track)} points")
    print("=" * 70)
    
    # Cleanup
    capture.close()

if __name__ == "__main__":
    try:
        asyncio.run(test_hid_multitouch())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
