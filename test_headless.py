#!/usr/bin/env python3
"""
Test Headless Mode

Quick test to verify the C# window is hidden.
"""

import time
from simple_windows_touchpad import SimpleTouchpadReader

print("="*60)
print("Testing Headless Mode")
print("="*60)
print("\nStarting touchpad reader in HEADLESS mode...")
print("The C# window should NOT appear!\n")

# Create reader in headless mode
reader = SimpleTouchpadReader(headless=True)

if not reader.start():
    print("✗ Failed to start")
    exit(1)

print("✓ Reader started in headless mode")
print("\nTouch your touchpad for 5 seconds...")
print("(If you see a C# window, headless mode is NOT working)\n")

start_time = time.time()
last_contact_count = 0

while time.time() - start_time < 5:
    contacts = reader.read_contacts()
    
    if contacts is not None and len(contacts) > 0:
        if len(contacts) != last_contact_count:
            print(f"✓ Detected {len(contacts)} finger(s)")
            last_contact_count = len(contacts)
    elif contacts is not None and len(contacts) == 0 and last_contact_count > 0:
        print("  Fingers lifted")
        last_contact_count = 0
    
    time.sleep(0.01)

reader.stop()

print("\n" + "="*60)
print("Test Complete!")
print("="*60)
print("\nDid you see a C# window?")
print("  NO  = ✓ Headless mode is working!")
print("  YES = ✗ Headless mode is NOT working - rebuild needed")
