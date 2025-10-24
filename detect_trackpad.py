#!/usr/bin/env python3
"""
Trackpad Detection Utility (Cross-Platform)

Automatically detects and lists all trackpad devices on the system.
Works on Linux and Windows.

Usage:
    python3 detect_trackpad.py
"""

import platform
from trackpad_lib import detect_trackpad, list_all_trackpads


def main():
    system = platform.system()
    
    print("🔍 Trackpad Detection Utility")
    print("=" * 60)
    print(f"Platform: {system}")
    print("=" * 60)
    
    # Try auto-detection
    print("\n1. Auto-detecting trackpad...")
    best_device = detect_trackpad()
    
    if best_device:
        if system == 'Windows':
            print(f"   ✓ Windows Precision Touchpad detected")
        else:
            print(f"   ✓ Best match: {best_device}")
    else:
        print("   ✗ No trackpad detected")
    
    # List all candidates
    print("\n2. All available trackpad devices:")
    devices = list_all_trackpads()
    
    if devices:
        for i, dev in enumerate(devices, 1):
            if system == 'Windows':
                print(f"   ⭐ {i}. {dev['path']}")
                print(f"      Name: {dev['name']}")
                print(f"      Max touches: {dev.get('max_touches', 'Unknown')}")
            else:
                marker = "⭐" if dev['path'] == best_device else "  "
                print(f"   {marker} {i}. {dev['path']}")
                print(f"      Name: {dev['name']}")
                print(f"      Score: {dev['score']}")
                print(f"      Trackpad name: {'Yes' if dev.get('is_trackpad_name', False) else 'No'}")
            print()
    else:
        print("   (none found)")
    
    # Usage instructions
    print("\n3. Usage:")
    if best_device:
        print(f"   Auto-detect (recommended):")
        print(f"     capture = TrackpadCapture()")
        print()
        if system == 'Linux':
            print(f"   Manual specification (Linux only):")
            print(f"     capture = TrackpadCapture(device_path='{best_device}')")
    else:
        if system == 'Linux':
            print("   No trackpad detected. Check permissions:")
            print("     sudo chmod a+r /dev/input/event*")
            print("   Or add yourself to input group:")
            print("     sudo usermod -a -G input $USER")
            print("     (then log out and log back in)")
        elif system == 'Windows':
            print("   No Windows Precision Touchpad detected.")
            print("   Make sure your device has touch support enabled.")
            print("   Check: Settings > Devices > Touchpad")
        else:
            print(f"   Platform '{system}' is not yet supported.")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
