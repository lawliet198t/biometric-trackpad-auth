#!/usr/bin/env python3
"""
Debug Headless Mode

Check if the --headless flag is being passed correctly.
"""

import subprocess
from pathlib import Path

# Find the exe
possible_paths = [
    "TouchpadCapture/bin/TouchpadCapture.exe",
    "TouchpadCapture.exe",
    "TouchpadCapture/bin/Release/net8.0-windows/TouchpadCapture.exe",
]

exe_path = None
for path in possible_paths:
    if Path(path).exists():
        exe_path = str(Path(path).absolute())
        break

if not exe_path:
    print("✗ TouchpadCapture.exe not found!")
    print("Searched:")
    for p in possible_paths:
        print(f"  - {p}")
    exit(1)

print("="*60)
print("Debug Headless Mode")
print("="*60)
print(f"\nFound executable: {exe_path}")

# Test 1: Run without --headless
print("\n" + "="*60)
print("Test 1: Running WITHOUT --headless flag")
print("="*60)
print("Command: TouchpadCapture.exe")
print("\nYou should see a window appear...")
input("Press ENTER to start (then close the window manually)...")

proc = subprocess.Popen(
    [exe_path],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

import time
time.sleep(2)

try:
    proc.terminate()
    proc.wait(timeout=2)
except:
    proc.kill()

print("✓ Test 1 complete")

# Test 2: Run with --headless
print("\n" + "="*60)
print("Test 2: Running WITH --headless flag")
print("="*60)
print("Command: TouchpadCapture.exe --headless")
print("\nYou should NOT see a window...")
input("Press ENTER to start (watch for 3 seconds)...")

proc = subprocess.Popen(
    [exe_path, "--headless"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Read first line to see if it says headless
line = proc.stdout.readline()
print(f"\nFirst output line: {line.strip()}")

if "headless" in line.lower():
    print("✓ Program recognized --headless flag!")
else:
    print("✗ Program did NOT recognize --headless flag!")
    print("  The executable may not be rebuilt correctly.")

time.sleep(3)

try:
    proc.terminate()
    proc.wait(timeout=2)
except:
    proc.kill()

print("\n" + "="*60)
print("Debug Complete")
print("="*60)
print("\nDid you see a window in Test 2?")
print("  NO  = ✓ Headless mode is working!")
print("  YES = ✗ Problem found - see below")
print("\nIf window appeared in Test 2:")
print("  1. The executable wasn't rebuilt")
print("  2. Or the build didn't include the new code")
print("  3. Check the 'First output line' above")
print("     - Should mention 'headless mode'")
