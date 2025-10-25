# Simple Windows Touchpad - Raw Values Only

Minimal implementation to get raw X, Y, ContactId values from Windows touchpad.

## Files

**Essential files only:**
- `simple_windows_touchpad.py` - Python reader (gets raw values)
- `TouchpadCapture/SimpleProgram.cs` - C# program (captures touch events)
- `simple_biometric_capture.py` - Example biometric integration
- `build_touchpad.bat` - Build script

## Quick Start

### 1. Build

```bash
build_touchpad.bat
```

This creates `TouchpadCapture.exe`

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
- **X, Y**: Raw pixel coordinates
- **Timestamp**: Unix timestamp in milliseconds

## That's It!

No complex abstractions. Just raw touchpad values you can use directly.

See `SIMPLE_TOUCHPAD.md` for more details.
