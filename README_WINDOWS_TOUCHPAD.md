# Windows Multi-Touch Setup

## Important Note

The pre-built releases only contain an **EXE file**, not a DLL. To use Python.NET, you need to **build from source**.

## Option 1: Build from Source (Recommended for Python.NET)

### Prerequisites
- .NET 6 SDK: https://dotnet.microsoft.com/download

### Steps

1. **Clone and build:**
   ```bash
   git clone https://github.com/emoacht/RawInput.Touchpad.git
   cd RawInput.Touchpad/Source
   dotnet build -c Release
   ```

2. **Copy DLL to your project:**
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

5. **Run:**
   ```bash
   python realtime_trainer.py
   ```

---

## Option 2: Use Pre-built EXE (Simpler, Test Only)

1. **Download:**
   - Go to: https://github.com/emoacht/RawInput.Touchpad/releases
   - Download `RawInput.Touchpad.exe`

2. **Run to test your touchpad:**
   ```bash
   RawInput.Touchpad.exe
   ```
   
   Touch your touchpad - you should see all 5 fingers!

3. **This confirms your touchpad works**, but you'll need Option 1 for Python integration.

---

## Option 3: Use Linux (Easiest!)

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
