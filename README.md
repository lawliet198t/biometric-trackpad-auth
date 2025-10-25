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

### 1. Build

```bash
build_rawinput.bat
```

This creates `TouchpadCapture.exe` using the Raw Input API

### 2. Run

```bash
# See raw values
python simple_windows_touchpad.py

# Or use in biometric system
python simple_biometric_capture.py
```

### 3. Touch Your Touchpad

Raw values appear:

```
[14:23:45] 2 contact(s):
  Contact 0: X=245.5, Y=312.8
  Contact 1: X=567.2, Y=423.1
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

## That's It!

No complex abstractions. Just raw touchpad values you can use directly.

See `SIMPLE_TOUCHPAD.md` for more details.
