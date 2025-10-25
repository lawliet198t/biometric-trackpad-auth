# Windows Multi-Touch Setup

## Automatic Setup (Recommended)

```bash
python setup_windows_touchpad.py
```

This will:
1. ✅ Check for git and .NET SDK
2. ✅ Clone the repository
3. ✅ Build the DLL from source
4. ✅ Install pythonnet
5. ✅ Verify everything works

**Prerequisites:**
- git: https://git-scm.com/download/win (or `winget install Git.Git`)
- .NET SDK: https://dotnet.microsoft.com/download (or `winget install Microsoft.DotNet.SDK.6`)

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
