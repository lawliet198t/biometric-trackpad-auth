# Windows Multi-Touch Setup

## Quick Start (1 Minute)

```bash
python setup_windows_touchpad.py
```

This automatically downloads the C# library, installs dependencies, and verifies everything works.

---

## What You Get

- ✅ TRUE multi-touch (all 5 fingers!)
- ✅ Automatic download and setup
- ✅ Works just like Linux version

---

## Manual Setup (if automatic fails)

1. **Install pythonnet:**
   ```bash
   pip install pythonnet
   ```

2. **Download C# library:**
   - Go to: https://github.com/emoacht/RawInput.Touchpad/releases
   - Download latest ZIP
   - Extract `RawInput.Touchpad.dll` to your project folder

3. **Test:**
   ```bash
   python test_windows_multitouch.py
   ```

4. **Run:**
   ```bash
   python realtime_trainer.py
   ```

---

## How It Works

```
Your Python Code
    ↓
Python.NET (pythonnet)
    ↓
RawInput.Touchpad.dll (C# library)
    ↓
Windows Raw Input API
    ↓
Your Touchpad (5+ fingers!)
```

---

## Troubleshooting

### "pythonnet not installed"
```bash
pip install pythonnet
```

### "DLL not found"
Run: `python setup_windows_touchpad.py`

Or download manually from: https://github.com/emoacht/RawInput.Touchpad/releases

### "Touchpad not detected"
Check: Settings → Devices → Touchpad  
Look for: "Your PC has a precision touchpad"

---

## Files

- `setup_windows_touchpad.py` - Auto-installer
- `windows_touchpad_pythonnet.py` - Python.NET wrapper
- `test_windows_multitouch.py` - Test suite
- `RawInput.Touchpad.dll` - C# library (auto-downloaded)

---

**That's it!** Run `python setup_windows_touchpad.py` and you're done! 🎉
