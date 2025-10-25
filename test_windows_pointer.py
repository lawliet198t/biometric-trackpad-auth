#!/usr/bin/env python3
"""
Test Windows Pointer Input API

Simple test to verify Windows Pointer Input is working with your touchpad.
"""

import asyncio
import time
from windows_touchpad import WindowsTouchpadCapture, detect_windows_touchpad

async def test_pointer_input():
    print("=" * 60)
    print("Windows Pointer Input API Test")
    print("=" * 60)
    print()
    
    # Detect touchpad
    print("1. Detecting touchpad...")
    if detect_windows_touchpad():
        print("   ✓ Touchpad detected!")
    else:
        print("   ⚠️  No touchpad detected, but will try anyway")
    print()
    
    # Create capture instance
    print("2. Initializing capture...")
    capture = WindowsTouchpadCapture()
    
    if not capture.open_device():
        print("   ✗ Failed to initialize")
        return
    
    print()
    print("3. Starting capture test...")
    print("   Touch your touchpad with 1-5 fingers")
    print("   Press Ctrl+C to stop")
    print()
    
    # Start capturing
    capture.start_capture()
    
    # Callbacks
    def on_finger_down(pointer_id):
        print(f"   ✓ Finger {pointer_id} detected")
    
    def on_finger_up(pointer_id, points):
        print(f"   ✓ Finger {pointer_id} lifted - {len(points)} points captured")
    
    # Run for 30 seconds or until Ctrl+C
    try:
        task = asyncio.create_task(
            capture.process_device_events(on_finger_down, on_finger_up)
        )
        
        start_time = time.time()
        while time.time() - start_time < 30:
            await asyncio.sleep(0.1)
            
            # Show active touches
            if capture.active_touches:
                active_count = len(capture.active_touches)
                print(f"   Active touches: {active_count}", end='\r')
        
        task.cancel()
        
    except KeyboardInterrupt:
        print("\n   Stopped by user")
    
    # Summary
    capture.stop_capture()
    all_tracks = capture.get_all_tracks()
    
    print()
    print("=" * 60)
    print("Test Summary:")
    print(f"  Total gestures captured: {len(all_tracks)}")
    for i, track in enumerate(all_tracks, 1):
        print(f"  Gesture {i}: {len(track)} points")
    print("=" * 60)
    
    # Cleanup
    capture.close()

if __name__ == "__main__":
    try:
        asyncio.run(test_pointer_input())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
