#!/usr/bin/env python3
"""
Test if --headless argument is being passed
"""

import subprocess
from pathlib import Path

# Find exe
exe_path = None
for path in ["TouchpadCapture/bin/TouchpadCapture.exe", "TouchpadCapture.exe"]:
    if Path(path).exists():
        exe_path = str(Path(path).absolute())
        break

if not exe_path:
    print("✗ Executable not found")
    exit(1)

print(f"Testing: {exe_path}")
print("\nStarting with --headless flag...")
print("Reading first output line...\n")

# Start process
proc = subprocess.Popen(
    [exe_path, "--headless"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

# Read first line
import time
time.sleep(0.5)

try:
    line = proc.stdout.readline()
    print(f"Output: {line.strip()}")
    
    if "headless" in line.lower():
        print("\n✓ SUCCESS: Program recognized --headless flag")
    else:
        print("\n✗ FAIL: Program did NOT recognize --headless flag")
        print("  The executable needs to be rebuilt")
except Exception as e:
    print(f"Error reading output: {e}")

# Cleanup
try:
    proc.terminate()
    proc.wait(timeout=2)
except:
    proc.kill()

print("\nDid you see a window?")
answer = input("(y/n): ").lower()

if answer == 'n':
    print("\n✓ Headless mode is working!")
else:
    print("\n✗ Headless mode is NOT working")
    print("\nPossible issues:")
    print("1. Executable wasn't rebuilt after code changes")
    print("2. Wrong executable is being used")
    print("3. WPF window shows briefly before hiding")
