# Windows Touchpad Biometric Authentication

Biometric authentication using Windows Precision Touchpad with the **Raw Input API**.

This system captures your unique touchpad usage patterns (finger movements, pressure, timing) to authenticate you. It uses the Raw Input API to get true multi-touch data directly from the touchpad hardware, based on [emoacht/RawInput.Touchpad](https://github.com/emoacht/RawInput.Touchpad).

## Features

- **True multi-touch**: Captures data from all fingers simultaneously
- **Raw coordinates**: Direct X, Y values from hardware (0-65535 range)
- **Contact tracking**: Tracks individual fingers across frames
- **High precision**: No OS processing or filtering
- **Biometric features**: Extracts unique patterns from your touchpad usage

## One-Command Setup (Windows)

```bash
setup_windows.bat
```

This will:
1. Check for .NET SDK (install if missing)
2. Create Python virtual environment
3. Install all dependencies
4. Build TouchpadCapture.exe
5. Run a quick test

**That's it!** Everything is configured and ready to use.

**→ See [QUICKSTART.md](QUICKSTART.md) for a complete 5-minute guide**

## Quick Start

### 1. Train Your Biometric Baseline

```bash
venv\Scripts\activate.bat
python windows_biometric_trainer.py
```

Follow the prompts to perform your gesture 5 times. The system will learn your unique pattern.

### 2. Test Authentication

After training, the script automatically enters verification mode. Try your gesture to authenticate!

### 3. View Raw Touchpad Data (Optional)

```bash
venv\Scripts\activate.bat
python simple_windows_touchpad.py
```

Touch your touchpad to see raw values:

```
[14:23:45] 2 finger(s): [0: X=32768, Y=16384] [1: X=45000, Y=20000]
```

## How It Works

### 1. Raw Input API
The Raw Input API provides direct access to HID (Human Interface Device) data:
- **Direct hardware access**: No OS filtering or gesture interpretation
- **True multi-touch**: Supports 5+ simultaneous contacts
- **High precision**: Full resolution from touchpad sensor
- **Low latency**: Minimal processing between hardware and your code

### 2. Biometric Feature Extraction
The system extracts unique patterns from your touchpad usage:
- **Duration**: How long you touch the pad
- **Number of fingers**: How many fingers you use
- **Velocity**: How fast you move your fingers
- **Path patterns**: The unique way you move across the pad
- **Coordinate variance**: Your movement consistency

### 3. Authentication
Your baseline is compared against new attempts using normalized distance metrics. If the pattern matches within threshold, you're authenticated!

## Project Structure

### Essential Files (For Users)
```
├── setup_windows.bat              # One-command complete setup ⭐
├── simple_windows_touchpad.py     # Core touchpad reader
├── windows_biometric_trainer.py   # Training & verification ⭐
├── test_simple.py                 # Quick test
├── TouchpadCapture/               # C# Raw Input API wrapper
│   ├── RawInputProgram.cs
│   └── RawInputProgram.csproj
└── requirements.txt               # Python dependencies
```

### Debugging/Development Files
```
├── build_rawinput.bat             # Rebuild TouchpadCapture.exe only
├── rebuild.bat                    # Clean rebuild
├── check_dotnet.bat               # Check .NET installation
├── verify_setup.bat               # Verify project files
├── setup_venv.bat                 # Setup Python venv only
├── test_biometric_windows.py      # Test biometric capture
├── simple_biometric_capture.py    # Biometric capture example
├── detect_trackpad.py             # Detect trackpad device
├── trackpad_lib.py                # Trackpad library
├── trackpad_visualizer.py         # Visualize touchpad input
├── realtime_trainer.py            # Alternative trainer
├── realtime_verify.py             # Alternative verifier
└── advanced_biometrics.py         # Advanced features
```

**For most users, you only need `setup_windows.bat` and `windows_biometric_trainer.py`!**

## Advanced Usage

### Use in Your Code

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

### Data Format

Each contact provides:
- **ContactId**: Unique ID for each finger (0, 1, 2, ...)
- **X, Y**: Raw coordinates from touchpad hardware (0-65535 range)
- **Timestamp**: Unix timestamp in milliseconds

## Troubleshooting

### .NET SDK Not Found
Install .NET SDK 8.0 or later from: https://dotnet.microsoft.com/download

### Python Not Found
Install Python 3.7+ from: https://www.python.org/downloads/

### TouchpadCapture.exe Not Working
Run the build manually:
```bash
cd TouchpadCapture
dotnet publish RawInputProgram.csproj -c Release -o bin
```

### No Touchpad Detected
Make sure you have a Windows Precision Touchpad. Check in:
Settings → Devices → Touchpad

## Debugging Tools

If you need to debug or test individual components:

- `test_simple.py` - Quick touchpad test
- `test_biometric_windows.py` - Test biometric capture
- `build_rawinput.bat` - Rebuild TouchpadCapture.exe only
- `check_dotnet.bat` - Check .NET installation

## Quick Reference

### First Time Setup
```bash
setup_windows.bat
```

### Train Your Biometric Pattern
```bash
venv\Scripts\activate.bat
python windows_biometric_trainer.py
```

### View Raw Touchpad Data
```bash
venv\Scripts\activate.bat
python simple_windows_touchpad.py
```

### Run Quick Test
```bash
venv\Scripts\activate.bat
python test_simple.py
```

### Rebuild TouchpadCapture.exe
```bash
build_rawinput.bat
```

## Files You Can Delete

If you want to clean up the project after setup, these files are only for debugging:
- `build_rawinput.bat`, `rebuild.bat`, `check_dotnet.bat`, `verify_setup.bat`
- `setup_venv.bat`, `setup_venv.sh`
- `test_biometric_windows.py`, `test_detection.py`
- `simple_biometric_capture.py`, `detect_trackpad.py`
- `trackpad_lib.py`, `trackpad_visualizer.py`
- `realtime_trainer.py`, `realtime_verify.py`
- `advanced_biometrics.py`, `simple_windows_touchpad_v2.py`

**Keep these:**
- `setup_windows.bat` (for reinstalling)
- `simple_windows_touchpad.py` (core library)
- `windows_biometric_trainer.py` (main program)
- `test_simple.py` (quick test)
- `TouchpadCapture/` folder (required)
- `requirements.txt` (required)

## Credits

Based on the excellent work by [@emoacht](https://github.com/emoacht/RawInput.Touchpad) for the Raw Input API implementation.
