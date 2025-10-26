#!/usr/bin/env python3
"""
Find C# Window - Debug Tool

Starts the C# program and finds its window title.
"""

import ctypes
import time
from simple_windows_touchpad import SimpleTouchpadReader

# Windows API
user32 = ctypes.windll.user32
EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
GetWindowText = user32.GetWindowTextW
GetWindowTextLength = user32.GetWindowTextLengthW
IsWindowVisible = user32.IsWindowVisible


def list_all_windows():
    """List all visible windows"""
    windows = []
    
    def foreach_window(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowText(hwnd, buff, length + 1)
                title = buff.value
                if title:
                    windows.append((hwnd, title))
        return True
    
    EnumWindows(EnumWindowsProc(foreach_window), 0)
    return windows


print("="*70)
print("Find C# Window - Debug Tool")
print("="*70)

# Get windows before starting
print("\n[1] Getting list of windows before starting C#...")
windows_before = set(w[1] for w in list_all_windows())
print(f"Found {len(windows_before)} windows")

# Start C# program
print("\n[2] Starting C# program...")
reader = SimpleTouchpadReader(headless=False)

if not reader.start():
    print("✗ Failed to start reader")
    exit(1)

print("✓ C# program started")

# Wait for window to appear
print("\n[3] Waiting for C# window to appear...")
time.sleep(2)

# Get windows after starting
print("\n[4] Getting list of windows after starting C#...")
windows_after = list_all_windows()

# Find new windows
print("\n[5] Looking for new windows...")
new_windows = []
for hwnd, title in windows_after:
    if title not in windows_before:
        new_windows.append((hwnd, title))

print("\n" + "="*70)
print("RESULTS")
print("="*70)

if new_windows:
    print(f"\n✓ Found {len(new_windows)} new window(s):\n")
    for hwnd, title in new_windows:
        print(f"  HWND: {hwnd}")
        print(f"  Title: '{title}'")
        print()
        
        if "touchpad" in title.lower() or "capture" in title.lower():
            print(f"  ✓✓✓ This is likely the C# window! ✓✓✓")
            print(f"\n  Use this title in embedded_window.py:")
            print(f'  window_title = "{title}"')
            print()
else:
    print("\n✗ No new windows found")
    print("\nPossible reasons:")
    print("  1. C# window didn't appear")
    print("  2. Window appeared and closed immediately")
    print("  3. Window is hidden/minimized")
    
    print("\n\nAll windows with 'touchpad' or 'capture' in title:")
    found_any = False
    for hwnd, title in windows_after:
        if "touchpad" in title.lower() or "capture" in title.lower():
            print(f"  HWND: {hwnd} - Title: '{title}'")
            found_any = True
    
    if not found_any:
        print("  (none found)")

print("\n" + "="*70)

# Keep running so you can see the window
print("\nC# program is still running.")
print("Check if you can see the C# window on your screen.")
input("\nPress ENTER to stop...")

reader.stop()
print("✓ Stopped")
