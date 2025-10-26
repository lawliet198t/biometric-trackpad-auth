# Headless Mode - Single Window

## What is Headless Mode?

On Windows, the C# process that captures touchpad data normally shows a small window. With **headless mode**, that window is completely hidden, so everything runs in your pygame window!

## How to Use

### Step 1: Rebuild (Windows only)

```bash
build_rawinput.bat
```

This rebuilds `TouchpadCapture.exe` with headless support.

### Step 2: Use in Your Code

```python
from trackpad_lib import TrackpadCapture

# Headless mode - no C# window!
capture = TrackpadCapture(headless=True)
```

That's it! The C# window won't appear.

## Examples

### Simple Demo
```bash
python simple_demo_headless.py
```

### Biometric Training (already uses headless mode)
```bash
python realtime_trainer.py
```

### Biometric Verification (already uses headless mode)
```bash
python realtime_verify.py --baseline baseline.pkl
```

## What Changed?

1. **C# Program**: Added `--headless` flag that hides the window
2. **trackpad_lib.py**: Added `headless=True` parameter to `TrackpadCapture`
3. **All examples updated**: Now use headless mode by default

## Technical Details

The C# window is still created (needed for Windows message pump), but it's:
- 1x1 pixel size
- Positioned off-screen (-10000, -10000)
- Hidden visibility
- Not shown in taskbar
- Never activated

This way the Raw Input API still works, but you don't see the window!

## Backward Compatibility

If you want the old behavior (show C# window):

```python
capture = TrackpadCapture(headless=False)
```

## Why Keep the Window at All?

Windows Raw Input API requires a window handle to receive `WM_INPUT` messages. The window provides the message pump, but doesn't need to be visible!
