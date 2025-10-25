# Windows Touchpad - Raw Input API

Direct access to Windows Precision Touchpad using the **Raw Input API**.

This implementation uses the actual HID (Human Interface Device) Raw Input API to get true multi-touch data directly from the touchpad hardware, based on [emoacht/RawInput.Touchpad](https://github.com/emoacht/RawInput.Touchpad).

## Files

**Essential files:**
- `simple_windows_touchpad.py` - Python reader (gets raw values)
- `TouchpadCapture/RawInputProgram.cs` - C# program using Raw Input API
- `simple_biometric_capture.py` - Example biometric integration
- `build_rawinput.bat` - Build script

## What is Raw Input API?

The Raw Input API is a Windows API that provides direct access to HID (Human Interface Device) data. For touchpads, this means:

- **True multi-touch**: Get data from all fingers simultaneously
- **Raw coordinates**: Direct X, Y values from hardware (typically 0-65535 range)
- **Contact IDs**: Track individual fingers across frames
- **High precision**: No OS processing or filtering

## Quick Start

**→ See [QUICK_START.md](QUICK_START.md) for detailed step-by-step guide**

### 1. Verify Setup

```bash
verify_setup.bat
```

### 2. Build

```bash
build_rawinput.bat
```

### 3. Test

```bash
python simple_windows_touchpad.py
```

Touch your touchpad and see raw values:

```
[14:23:45] 2 contact(s):
  Contact 0: X=32768, Y=16384
  Contact 1: X=45000, Y=20000
```

## Use in Your Code

```python
from simple_windows_touchpad import SimpleTouchpadReader

reader = SimpleTouchpadReader()
reader.start()

while True:
    contacts = reader.read_contacts()
    
    if contacts:
        for c in contacts:
            print(f"Finger {c['ContactId']}: ({c['X']}, {c['Y']})")
    
    time.sleep(0.016)

reader.stop()
```

## What You Get

- **ContactId**: Unique ID for each finger (0, 1, 2, ...)
- **X, Y**: Raw coordinates from touchpad hardware (0-65535 range typically)
- **Timestamp**: Unix timestamp in milliseconds

## Why Raw Input API?

This is the **proper way** to access touchpad data on Windows:

1. **Direct hardware access**: No OS filtering or gesture interpretation
2. **True multi-touch**: Supports 5+ simultaneous contacts
3. **High precision**: Full resolution from touchpad sensor
4. **Low latency**: Minimal processing between hardware and your code

Based on the excellent work by [@emoacht](https://github.com/emoacht/RawInput.Touchpad).

## Documentation

- **[QUICK_START.md](QUICK_START.md)** - Step-by-step setup guide
- **[BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)** - Detailed build help
- **[RAW_INPUT_GUIDE.md](RAW_INPUT_GUIDE.md)** - How Raw Input API works
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical details
- **[FINAL_SUMMARY.md](FINAL_SUMMARY.md)** - Complete overview

## Troubleshooting

See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for common issues and solutions.

## That's It!

No complex abstractions. Just raw touchpad values directly from the hardware using the proper Windows Raw Input API.
