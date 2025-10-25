# Windows Integration Guide

## Important: Window Must Stay Open

The TouchpadCapture window **must stay open** to receive touchpad input. This is a Windows limitation - the Raw Input API requires a window to receive messages.

## What I Fixed

### 1. Window Always-On-Top
- Window now stays on top of other windows
- Positioned in top-right corner
- Won't get hidden behind other apps

### 2. Background Input (RIDEV_INPUTSINK)
- Window receives input even when not focused
- You can work in other windows while it captures
- **Note**: Window must still be visible (not minimized)

### 3. Integrated with Biometric System
- Created Windows-specific biometric trainer
- Simple test script to verify integration
- Works with your existing feature extraction

## Rebuild Required

Since we changed the C# code:

```cmd
rebuild.bat
```

## New Files Created

### 1. `test_biometric_windows.py`
Simple test to verify Windows touchpad works with biometric capture.

```cmd
python test_biometric_windows.py
```

### 2. `windows_biometric_trainer.py`
Complete biometric authentication system for Windows.

```cmd
python windows_biometric_trainer.py
```

## How to Use

### Quick Test

```cmd
# 1. Rebuild
rebuild.bat

# 2. Test basic capture
python test_biometric_windows.py
```

### Full Biometric Training

```cmd
# 1. Run trainer
python windows_biometric_trainer.py

# 2. Follow prompts:
#    - Perform gesture 5 times (training)
#    - Try to authenticate

# 3. Baseline saved to windows_baseline.pkl
```

## Window Behavior

### What You'll See

1. **Black window** appears in top-right corner
2. **Always on top** - won't get hidden
3. **Shows finger positions** in real-time
4. **Must stay open** for capture to work

### Why It Must Stay Open

Windows Raw Input API requires:
- A window handle to register for input
- Window must be visible (not minimized)
- Window receives WM_INPUT messages

**This is a Windows limitation, not a bug!**

## Workarounds

### Option 1: Keep Window Open (Recommended)
- Window is small and stays in corner
- Always-on-top so it won't get hidden
- Shows what's happening (useful for debugging)

### Option 2: Minimize to Tray (Future)
Could create a system tray app that:
- Runs in background
- Shows icon in system tray
- Hidden window still receives input

### Option 3: Windows Service (Complex)
Could run as Windows service, but:
- Requires admin privileges
- More complex setup
- Not recommended for this use case

## Integration with Your Programs

### Using with `realtime_trainer.py`

The `trackpad_lib.py` already supports Windows via `SimpleTouchpadReader`.

Just run:
```cmd
python realtime_trainer.py
```

The TouchpadCapture window will open automatically.

### Using with `realtime_verify.py`

Same as above:
```cmd
python realtime_verify.py
```

### Custom Integration

```python
from simple_windows_touchpad import SimpleTouchpadReader

# Start reader (window opens)
reader = SimpleTouchpadReader()
reader.start()

# Capture gesture
gesture_samples = []
start_time = time.time()

while time.time() - start_time < 2.0:
    contacts = reader.read_contacts()
    
    if contacts and len(contacts) > 0:
        sample = {
            'time': time.time(),
            'contacts': [
                {'id': c['ContactId'], 'x': c['X'], 'y': c['Y']}
                for c in contacts
            ]
        }
        gesture_samples.append(sample)
    
    time.sleep(0.016)

# Extract features and verify
# ... your code here ...

reader.stop()
```

## Tips

### 1. Position the Window
- Window appears in top-right by default
- You can move it anywhere
- It will stay on top

### 2. Don't Minimize
- Minimizing stops input capture
- Keep it visible (even if small)

### 3. Multiple Monitors
- Window appears on primary monitor
- You can drag it to any monitor

### 4. During Capture
- You can work in other windows
- Just keep TouchpadCapture window visible
- Touch your touchpad normally

## Comparison: Windows vs Linux

| Feature | Linux | Windows |
|---------|-------|---------|
| Background capture | ✓ Yes | ⚠️ Window must be visible |
| Multi-touch | ✓ Yes | ✓ Yes |
| Raw coordinates | ✓ Yes | ✓ Yes |
| Contact IDs | ✓ Yes | ✓ Yes |
| Setup complexity | Medium | Easy |

## Testing

### Test 1: Basic Capture
```cmd
python simple_windows_touchpad.py
```

Expected: See finger positions in real-time

### Test 2: Biometric Integration
```cmd
python test_biometric_windows.py
```

Expected: Capture gesture and extract features

### Test 3: Full Training
```cmd
python windows_biometric_trainer.py
```

Expected: Train and verify authentication

## Troubleshooting

### Window Disappears
- Check if minimized (restore it)
- Check if behind other windows (it should be on top)
- Restart the program

### No Input Captured
- Make sure window is visible
- Don't minimize the window
- Touch the touchpad (not click mouse)

### Window Not Always-On-Top
- Rebuild: `rebuild.bat`
- Some apps can override always-on-top
- Try moving window to different position

## Next Steps

1. **Rebuild**: `rebuild.bat`
2. **Test**: `python test_biometric_windows.py`
3. **Train**: `python windows_biometric_trainer.py`
4. **Integrate**: Use in your biometric system

The window requirement is a Windows limitation, but the always-on-top feature makes it manageable!
