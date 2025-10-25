# Windows Multi-Touch Setup Guide

Complete step-by-step guide to enable TRUE multi-touch on Windows.

## Prerequisites

- Windows 10/11
- Windows Precision Touchpad (check: Settings → Devices → Touchpad)
- Python 3.7+

## Step 1: Install Python.NET

```bash
pip install pythonnet
```

Or if using virtual environment:
```bash
# Activate your venv first
venv\Scripts\activate.bat

# Then install
pip install pythonnet
```

## Step 2: Get the C# Library

### Option A: Download Pre-built (Easiest)

1. Go to: https://github.com/emoacht/RawInput.Touchpad/releases
2. Download the latest release (e.g., `RawInput.Touchpad_1.0.0.zip`)
3. Extract the ZIP file
4. Find `RawInput.Touchpad.dll` in the extracted files
5. Copy it to your project folder (same directory as `realtime_trainer.py`)

### Option B: Build from Source

```bash
# Clone the repository
git clone https://github.com/emoacht/RawInput.Touchpad.git
cd RawInput.Touchpad/Source

# Build with .NET
dotnet build -c Release

# Copy the DLL
copy bin\Release\net6.0\RawInput.Touchpad.dll ..\..\your-project-folder\
```

## Step 3: Test the C# Library

Before integrating with Python, test that the C# library works:

1. Run `RawInput.Touchpad.exe` (from the release)
2. Touch your touchpad with multiple fingers
3. You should see:
   - Contact ID for each finger
   - X, Y coordinates
   - Real-time updates

**If this doesn't work, your touchpad may not support Raw Input API.**

## Step 4: Verify Python Integration

Test that Python can load the C# library:

```python
# test_pythonnet.py
import clr
from pathlib import Path

dll_path = Path("RawInput.Touchpad.dll").absolute()
print(f"Loading: {dll_path}")

try:
    clr.AddReference(str(dll_path))
    print("✓ DLL loaded successfully!")
    
    # Try to import
    from RawInput.Touchpad import TouchpadForm
    print("✓ Classes imported successfully!")
    
except Exception as e:
    print(f"✗ Error: {e}")
```

Run it:
```bash
python test_pythonnet.py
```

## Step 5: Update Your Project

The code is already set up! Just make sure:

1. ✅ `pythonnet` is installed
2. ✅ `RawInput.Touchpad.dll` is in your project folder
3. ✅ Your touchpad is a Windows Precision Touchpad

## Step 6: Test Multi-Touch

```bash
# Run the trainer
python realtime_trainer.py

# You should see:
# "✓ Using Python.NET multi-touch backend"
# "🎉 TRUE MULTI-TOUCH ENABLED!"

# Touch your touchpad with multiple fingers
# Each finger should be detected separately!
```

## Troubleshooting

### "pythonnet not installed"

```bash
pip install pythonnet
```

### "RawInput.Touchpad.dll not found"

Make sure the DLL is in:
- Same folder as your Python scripts, OR
- In a `lib/` subfolder, OR
- In a `bin/` subfolder

### "Could not import touchpad classes"

The DLL structure might be different. Check the actual namespace:

```python
import clr
clr.AddReference("RawInput.Touchpad.dll")

# List all types in the assembly
import System
assembly = clr.System.Reflection.Assembly.LoadFrom("RawInput.Touchpad.dll")
for type in assembly.GetTypes():
    print(type.FullName)
```

Then update `windows_touchpad_pythonnet.py` with the correct namespace.

### "Touchpad not detected"

1. Check Windows Settings → Devices → Touchpad
2. Make sure "Touchpad" is enabled
3. Look for "Your PC has a precision touchpad" message
4. If not present, your touchpad may not support Precision Touchpad API

### Still using mouse simulation

Check the console output when running your trainer:
- ✓ "Using Python.NET multi-touch backend" = Working!
- ⚠️ "Using mouse simulation" = Fallback mode

If in fallback mode:
1. Check pythonnet is installed: `pip list | grep pythonnet`
2. Check DLL exists: `dir RawInput.Touchpad.dll`
3. Check for error messages in console

## File Structure

Your project should look like:
```
your-project/
├── realtime_trainer.py
├── realtime_verify.py
├── trackpad_lib.py
├── windows_touchpad_pythonnet.py
├── RawInput.Touchpad.dll          ← C# library
├── requirements.txt
└── README_WINDOWS_TOUCHPAD.md
```

## Verification Checklist

- [ ] Python.NET installed (`pip list | grep pythonnet`)
- [ ] DLL file present (`dir RawInput.Touchpad.dll`)
- [ ] C# app works standalone (shows multiple fingers)
- [ ] Python can load DLL (`python test_pythonnet.py`)
- [ ] Trainer shows "Using Python.NET multi-touch backend"
- [ ] Multiple fingers detected when touching touchpad

## Success!

If everything works, you should see:
```
✓ Using Python.NET multi-touch backend
✓ C# library loaded successfully
✓ Windows Precision Touchpad initialized via Python.NET
  Using emoacht's RawInput.Touchpad library

🎉 TRUE MULTI-TOUCH ENABLED!
  Touch your touchpad with multiple fingers

👇 Finger 0 down at (234.5, 456.7)
👇 Finger 1 down at (345.6, 567.8)
👇 Finger 2 down at (456.7, 678.9)
```

Now your biometric trainer has true multi-touch on Windows! 🎉

## Need Help?

1. Check console output for error messages
2. Verify each step in the checklist
3. Test the C# app standalone first
4. Check that your touchpad is a Precision Touchpad

## Alternative: Subprocess Method

If Python.NET doesn't work, you can use the subprocess method:
- See `windows_touchpad_csharp.py`
- Requires building a C# console app
- Simpler but less elegant
