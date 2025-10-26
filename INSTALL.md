# Installation Guide

## Quick Install (Recommended)

Run the one-command setup:

```bash
setup_windows.bat
```

This automatically:
1. Checks for .NET SDK
2. Creates Python virtual environment
3. Installs dependencies
4. Builds TouchpadCapture.exe
5. Runs a test

## Manual Installation

If you prefer to install step-by-step:

### 1. Install Prerequisites

**Python 3.7+**
- Download from: https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

**.NET SDK 8.0+**
- Download from: https://dotnet.microsoft.com/download
- Install the SDK (not just runtime)

### 2. Setup Python Environment

```bash
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 3. Build TouchpadCapture

```bash
cd TouchpadCapture
dotnet publish RawInputProgram.csproj -c Release -o bin
cd ..
```

### 4. Test

```bash
python test_simple.py
```

## Troubleshooting

### .NET SDK Not Found

Install from: https://dotnet.microsoft.com/download

Verify installation:
```bash
dotnet --version
```

### Python Not Found

Install from: https://www.python.org/downloads/

Verify installation:
```bash
python --version
```

### Build Fails

Make sure you have .NET SDK (not just runtime):
```bash
dotnet --list-sdks
```

### No Touchpad Detected

Check if you have a Windows Precision Touchpad:
- Settings → Devices → Touchpad
- Look for "Precision Touchpad" section

## Next Steps

After installation:

1. **Train your baseline:**
   ```bash
   venv\Scripts\activate.bat
   python windows_biometric_trainer.py
   ```

2. **Test authentication:**
   The trainer automatically enters verification mode after training.

3. **View raw data (optional):**
   ```bash
   python simple_windows_touchpad.py
   ```
