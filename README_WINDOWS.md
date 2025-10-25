# Windows Multi-Touch Setup

## Quick Start

1. **Build the C# app:**
   ```bash
   build_touchpad.bat
   ```

2. **Run your Python app:**
   ```bash
   python realtime_trainer.py
   ```

That's it! True multi-touch support via C# subprocess.

## How It Works

```
Python (realtime_trainer.py)
    ↓
windows_touchpad_subprocess.py
    ↓ subprocess
TouchpadCapture.exe (C#)
    ↓ uses
RawInput.Touchpad.dll (emoacht's library)
    ↓ accesses
Windows Raw Input API
    ↓ reads
Precision Touchpad Hardware
```

## Files

- `TouchpadCapture/` - C# console app source
- `build_touchpad.bat` - Builds everything automatically
- `windows_touchpad_subprocess.py` - Python wrapper
- `TouchpadCapture.exe` - Built C# app (after running build script)

## Why This Works

- ✅ No Python.NET complexity
- ✅ No WPF loading issues
- ✅ Simple JSON communication
- ✅ True multi-touch support
- ✅ Clean separation of concerns

## Troubleshooting

**"TouchpadCapture.exe not found"**
- Run: `build_touchpad.bat`

**"git not found"**
- Install: `winget install Git.Git`

**".NET SDK not found"**
- Install: `winget install Microsoft.DotNet.SDK.8`

## Alternative: Use Linux

Linux works out of the box with zero setup:
```bash
python realtime_trainer.py
```

No building, no DLLs, no complexity.
