# Biometric Trackpad Authentication - Setup Guide

## Linux (Recommended - Zero Setup!)

```bash
python realtime_trainer.py
```

That's it! Multi-touch works out of the box.

## Windows (Requires Build)

### One-Time Setup

1. **Install prerequisites** (if not already installed):
   ```bash
   winget install Git.Git
   winget install Microsoft.DotNet.SDK.8
   ```

2. **Build the C# touchpad capture app:**
   ```bash
   build_touchpad.bat
   ```

3. **Run your app:**
   ```bash
   python realtime_trainer.py
   ```

### What Gets Built

- `TouchpadCapture.exe` - C# console app that captures touchpad data
- `RawInput.Touchpad.dll` - emoacht's library for Windows Raw Input API

### How It Works

```
Python → Subprocess → C# EXE → Raw Input API → Touchpad
```

Simple JSON communication, no Python.NET complexity!

## Files Overview

### Core Application
- `realtime_trainer.py` - Main training application
- `realtime_verify.py` - Verification application
- `trackpad_lib.py` - Cross-platform trackpad library

### Windows Support
- `TouchpadCapture/` - C# console app source
- `build_touchpad.bat` - Automated build script
- `windows_touchpad_subprocess.py` - Python subprocess wrapper
- `windows_touchpad.py` - Fallback mouse simulation

### Documentation
- `README.md` - Main project README
- `README_WINDOWS.md` - Windows-specific details
- `SETUP.md` - This file

## Troubleshooting

### Windows: "TouchpadCapture.exe not found"
Run: `build_touchpad.bat`

### Windows: Build fails
- Make sure git is installed: `git --version`
- Make sure .NET SDK is installed: `dotnet --version`
- Restart terminal after installing

### Linux: "evdev not installed"
```bash
pip install evdev
```

### Any Platform: "No touchpad detected"
- Check Settings → Touchpad
- Make sure it's a Precision Touchpad (Windows) or multi-touch device (Linux)

## Why This Approach?

We tried Python.NET but encountered:
- ✗ WPF assembly loading issues
- ✗ TypeLoadException errors
- ✗ Complex dependency chains
- ✗ .NET 5+ compatibility problems

The subprocess approach is:
- ✅ Simple and reliable
- ✅ Clean separation
- ✅ Easy to debug
- ✅ No Python.NET needed
