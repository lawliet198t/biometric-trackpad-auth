#!/usr/bin/env python3
"""
Simple Demo - Headless Mode

Uses the existing trackpad_lib.py with headless mode.
The C# window won't appear - everything runs in the pygame window!
"""

import asyncio
from trackpad_lib import TrackpadCapture, GestureVisualizer, run_capture_loop


async def main():
    # Create capture with headless=True (no C# window!)
    capture = TrackpadCapture(headless=True)
    
    # Create visualizer
    visualizer = GestureVisualizer(
        width=1200,
        height=800,
        title="Touchpad Demo (Headless Mode)"
    )
    
    # Callback when gesture complete
    async def on_gesture_complete(tracks):
        print(f"\n✓ Gesture captured with {len(tracks)} finger(s)")
        for i, track in enumerate(tracks):
            print(f"  Finger {i+1}: {len(track.points)} points")
    
    # Set status
    visualizer.set_status("Touch your trackpad!", (0, 255, 100))
    visualizer.set_info_lines([
        "Press SPACE to capture gesture",
        "C# window is hidden (headless mode)",
        "Everything runs in this window!"
    ])
    
    print("="*60)
    print("Simple Demo - Headless Mode")
    print("="*60)
    print("\nThe C# window is hidden!")
    print("Touch your trackpad to see visualization.")
    print("Press SPACE to capture a gesture.\n")
    
    # Run
    await run_capture_loop(capture, visualizer, on_gesture_complete)


if __name__ == "__main__":
    asyncio.run(main())
