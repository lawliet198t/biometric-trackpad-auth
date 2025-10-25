#!/usr/bin/env python3
"""
Test Windows Setup

Checks if everything is ready for Windows multi-touch.
"""

import sys
from pathlib import Path
import subprocess

def check_file(path, description):
    """Check if a file exists"""
    if Path(path).exists():
        print(f"✓ {description}: {path}")
        return True
    else:
        print(f"✗ {description} not found: {path}")
        return False

def check_command(cmd, description):
    """Check if a command is available"""
    try:
        result = subprocess.run(
            [cmd, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            print(f"✓ {description}: {version}")
            return True
    except:
        pass
    
    print(f"✗ {description} not found")
    return False

def main():
    print("=" * 70)
    print("Windows Multi-Touch Setup Check")
    print("=" * 70)
    print()
    
    results = []
    
    # Check prerequisites
    print("Prerequisites:")
    results.append(check_command("git", "Git"))
    results.append(check_command("dotnet", ".NET SDK"))
    print()
    
    # Check if built
    print("Built files:")
    has_exe = check_file("TouchpadCapture.exe", "TouchpadCapture.exe")
    has_dll = check_file("RawInput.Touchpad.dll", "RawInput.Touchpad.dll")
    results.append(has_exe)
    results.append(has_dll)
    print()
    
    # Check source files
    print("Source files:")
    results.append(check_file("TouchpadCapture/Program.cs", "C# source"))
    results.append(check_file("TouchpadCapture/TouchpadCapture.csproj", "C# project"))
    results.append(check_file("windows_touchpad_subprocess.py", "Python wrapper"))
    print()
    
    # Summary
    print("=" * 70)
    if all(results):
        print("✓ Everything is ready!")
        print()
        print("Run: python realtime_trainer.py")
    elif has_exe and has_dll:
        print("✓ Built files exist - you're ready to run!")
        print()
        print("Run: python realtime_trainer.py")
    else:
        print("⚠️  Setup incomplete")
        print()
        if not (has_exe and has_dll):
            print("Run: build_touchpad.bat")
        print()
    print("=" * 70)

if __name__ == "__main__":
    main()
