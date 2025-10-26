#!/usr/bin/env python3
"""
Final Comprehensive Headless Test

This will tell you exactly what's wrong.
"""

import subprocess
import time
from pathlib import Path

print("="*70)
print("COMPREHENSIVE HEADLESS MODE TEST")
print("="*70)

# Step 1: Find executable
print("\n[Step 1] Finding executable...")
exe_path = None
search_paths = [
    "TouchpadCapture/bin/TouchpadCapture.exe",
    "TouchpadCapture/bin/RawInputProgram.exe",
    "TouchpadCapture.exe",
    "RawInputProgram.exe",
]

for path in search_paths:
    if Path(path).exists():
        exe_path = str(Path(path).absolute())
        print(f"✓ Found: {exe_path}")
        
        # Check file timestamp
        mtime = Path(path).stat().st_mtime
        age_seconds = time.time() - mtime
        age_minutes = age_seconds / 60
        
        print(f"  Last modified: {age_minutes:.1f} minutes ago")
        
        if age_minutes > 10:
            print(f"  ⚠️  WARNING: File is {age_minutes:.1f} minutes old")
            print(f"     Did you rebuild recently?")
        break

if not exe_path:
    print("✗ Executable not found!")
    print("\nSearched:")
    for p in search_paths:
        print(f"  - {p}")
    print("\nRun: build_rawinput.bat")
    exit(1)

# Step 2: Test without --headless
print("\n[Step 2] Testing WITHOUT --headless flag...")
print("Starting process...")

proc = subprocess.Popen(
    [exe_path],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

time.sleep(1)

# Read stderr for debug output
stderr_output = []
try:
    while True:
        line = proc.stderr.readline()
        if not line:
            break
        stderr_output.append(line.strip())
        if len(stderr_output) >= 5:
            break
except:
    pass

if stderr_output:
    print("Debug output:")
    for line in stderr_output:
        print(f"  {line}")

try:
    proc.terminate()
    proc.wait(timeout=2)
except:
    proc.kill()

print("✓ Test 2 complete")

# Step 3: Test WITH --headless
print("\n[Step 3] Testing WITH --headless flag...")
print("Command: TouchpadCapture.exe --headless")
print("\n⚠️  WATCH YOUR SCREEN NOW!")
print("Does a window appear? (even briefly?)")
print("\nStarting in 3 seconds...")
time.sleep(3)

proc = subprocess.Popen(
    [exe_path, "--headless"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

# Read stderr for debug output
time.sleep(0.5)
stderr_output = []
try:
    while True:
        line = proc.stderr.readline()
        if not line:
            break
        stderr_output.append(line.strip())
        if len(stderr_output) >= 5:
            break
except:
    pass

print("\nDebug output:")
if stderr_output:
    for line in stderr_output:
        print(f"  {line}")
        if "Headless mode ENABLED" in line:
            print("  ✓ Program recognized --headless flag!")
        elif "Headless mode DISABLED" in line:
            print("  ✗ Program did NOT recognize --headless flag!")
else:
    print("  (no debug output - executable may be old)")

# Read first JSON output
try:
    stdout_line = proc.stdout.readline()
    print(f"\nFirst output: {stdout_line.strip()}")
    if "headless" in stdout_line.lower():
        print("✓ Output mentions headless mode")
except:
    pass

time.sleep(2)

try:
    proc.terminate()
    proc.wait(timeout=2)
except:
    proc.kill()

# Step 4: Ask user
print("\n" + "="*70)
print("RESULTS")
print("="*70)

print("\nIn Step 3, did you see a window appear?")
print("  (even if it disappeared quickly)")
answer = input("\nDid you see a window? (y/n): ").lower()

print("\n" + "="*70)
if answer == 'n':
    print("✓✓✓ HEADLESS MODE IS WORKING! ✓✓✓")
    print("="*70)
    print("\nThe C# window is hidden successfully.")
    print("You can now use:")
    print("  python simple_demo_headless.py")
    print("  python realtime_trainer.py")
else:
    print("✗✗✗ HEADLESS MODE IS NOT WORKING ✗✗✗")
    print("="*70)
    print("\nPossible causes:")
    print("\n1. Executable wasn't rebuilt:")
    print("   - Run: build_rawinput.bat")
    print("   - Check file timestamp above")
    print("\n2. Wrong executable being used:")
    print(f"   - Using: {exe_path}")
    print("   - Should be in TouchpadCapture/bin/")
    print("\n3. Code changes didn't compile:")
    print("   - Check for build errors")
    print("   - Look at debug output above")
    print("\n4. WPF limitation:")
    print("   - Window may flash briefly (< 0.5 sec)")
    print("   - This is a WPF limitation")
    print("   - If it disappears quickly, it's working!")

print("\n" + "="*70)
