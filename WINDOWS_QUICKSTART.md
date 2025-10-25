# Windows Multi-Touch Quick Start

Get true multi-touch working in 5 minutes!

## 1. Install Python.NET

```bash
pip install pythonnet
```

## 2. Download C# Library

https://github.com/emoacht/RawInput.Touchpad/releases

Extract and copy `RawInput.Touchpad.dll` to your project folder.

## 3. Test Setup

```bash
python test_windows_multitouch.py
```

Should show: `🎉 ALL TESTS PASSED!`

## 4. Run Your Trainer

```bash
python realtime_trainer.py
```

Should show:
```
✓ Using Python.NET multi-touch backend
🎉 TRUE MULTI-TOUCH ENABLED!
```

## 5. Touch Your Touchpad!

Touch with multiple fingers - each finger is detected separately!

---

## Troubleshooting

### ✗ pythonnet not installed
```bash
pip install pythonnet
```

### ✗ DLL not found
Download from: https://github.com/emoacht/RawInput.Touchpad/releases  
Place `RawInput.Touchpad.dll` in project folder

### ✗ Touchpad not detected
Check: Settings → Devices → Touchpad  
Look for: "Your PC has a precision touchpad"

---

## Files You Need

```
your-project/
├── realtime_trainer.py
├── trackpad_lib.py
├── windows_touchpad_pythonnet.py
└── RawInput.Touchpad.dll          ← Download this!
```

---

## Full Guide

See `SETUP_WINDOWS_MULTITOUCH.md` for detailed instructions.

---

**That's it! 🎉**
