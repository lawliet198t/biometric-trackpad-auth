# Quick Start Guide

Get up and running with Windows Touchpad Biometric Authentication in 5 minutes!

## Prerequisites

- Windows 10 or 11
- Windows Precision Touchpad
- Python 3.7+
- .NET SDK 8.0+

## Step 1: Setup (One Command)

Open Command Prompt or PowerShell in the project directory and run:

```bash
setup_windows.bat
```

This will:
- ✓ Check for .NET SDK
- ✓ Create Python virtual environment
- ✓ Install dependencies
- ✓ Build TouchpadCapture.exe
- ✓ Run a quick test

**Time:** 2-3 minutes

## Step 2: Train Your Biometric Baseline

```bash
venv\Scripts\activate.bat
python windows_biometric_trainer.py
```

Follow the prompts:
1. Perform your gesture 5 times (be consistent!)
2. The system learns your unique pattern
3. Your baseline is saved to `windows_baseline.pkl`

**Tips for best results:**
- Use 2-3 fingers
- Make a distinctive pattern (circle, zigzag, etc.)
- Be consistent in speed and pressure
- Practice the same gesture each time

**Time:** 2-3 minutes

## Step 3: Test Authentication

After training, the script automatically enters verification mode.

Try your gesture to authenticate:
- ✓ **AUTHENTICATED** - Your pattern matches!
- ✗ **REJECTED** - Pattern doesn't match

**Time:** 30 seconds per attempt

## What You Get

Each contact provides:
- **ContactId**: Unique finger identifier
- **X, Y**: Raw coordinates (0-65535 range)
- **Timestamp**: Millisecond precision

The system extracts:
- Duration of gesture
- Number of fingers used
- Velocity patterns
- Path characteristics
- Movement consistency

## Common Commands

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

### Retrain Baseline
```bash
venv\Scripts\activate.bat
python windows_biometric_trainer.py
```
Choose "t" when prompted to train a new baseline.

### Rebuild TouchpadCapture.exe
```bash
build_rawinput.bat
```

## Troubleshooting

### Setup fails with ".NET SDK not found"
Install .NET SDK 8.0+ from: https://dotnet.microsoft.com/download

### Setup fails with "Python not found"
Install Python 3.7+ from: https://www.python.org/downloads/
Make sure to check "Add Python to PATH" during installation.

### "No touchpad detected" during test
Check if you have a Windows Precision Touchpad:
- Settings → Devices → Touchpad
- Look for "Precision Touchpad" section

### TouchpadCapture.exe doesn't work
Try rebuilding:
```bash
rebuild.bat
```

### Authentication always fails
- Make sure you're performing the same gesture consistently
- Try retraining with more deliberate, slower movements
- Use a more distinctive pattern

## Tips for Better Accuracy

1. **Consistent Speed**: Move at the same speed each time
2. **Same Pattern**: Use the exact same path/shape
3. **Same Fingers**: Use the same number of fingers
4. **Practice**: Do a few practice runs before training
5. **Environment**: Use the same hand position and angle

## Next Steps

- Read the full [README.md](README.md) for more details
- Check [INSTALL.md](INSTALL.md) for manual installation
- See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute

## Need Help?

- Check the [Troubleshooting section](README.md#troubleshooting) in README
- Open an issue on GitHub
- Review the debugging files in the project

## That's It!

You now have a working biometric authentication system using your touchpad. Enjoy! 🎉
