# Windows Multi-Touch Setup

## Automatic Setup (One Command!)

```bash
python setup_windows_touchpad.py
```

This will **automatically**:
1. ✅ Install git (if missing)
2. ✅ Install .NET SDK (if missing)
3. ✅ Clone the repository
4. ✅ Build the DLL from source
5. ✅ Install pythonnet
6. ✅ Verify everything works

**No manual downloads needed!** The script installs everything automatically using winget.

---

## Manual Setup (if automatic fails)

1. **Clone and build:**
   ```bash
   git clone https://github.com/emoacht/RawInput.Touchpad.git
   cd RawInput.Touchpad/Source
   dotnet build -c Release
   ```

2. **Copy DLL:**
   ```bash
   copy bin\Release\net6.0\RawInput.Touchpad.dll ..\..\your-project\
   ```

3. **Install pythonnet:**
   ```bash
   pip install pythonnet
   ```

4. **Test:**
   ```bash
   python test_windows_multitouch.py
   ```

---

## Use Linux (Easiest!)

Your touchpad already works perfectly on Linux:
```bash
python realtime_trainer.py  # Just works!
```

No setup needed on Linux! ✅

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
