# Installation Guide

## Platform Requirements

⚠️ **This software currently only supports Linux**. Windows and macOS are not supported due to the dependency on Linux's `evdev` interface.

### Supported Linux Distributions
- Ubuntu 18.04+
- Debian 10+
- Fedora 30+
- Arch Linux
- Other Linux distributions with Python 3.7+ and evdev support

## Prerequisites

### 1. Python 3.7 or higher

Check your Python version:
```bash
python3 --version
```

If you need to install Python:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# Fedora
sudo dnf install python3 python3-pip

# Arch Linux
sudo pacman -S python python-pip
```

### 2. System Dependencies

Install required system packages:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3-dev libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
```

**Fedora:**
```bash
sudo dnf install python3-devel SDL2-devel SDL2_image-devel SDL2_mixer-devel SDL2_ttf-devel
```

**Arch Linux:**
```bash
sudo pacman -S python sdl2 sdl2_image sdl2_mixer sdl2_ttf
```

## Installation Methods

### Method 1: Using pip (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/biometric-trackpad-auth.git
cd biometric-trackpad-auth
```

2. **Install Python dependencies:**
```bash
pip3 install -r requirements.txt
```

3. **Verify installation:**
```bash
python3 trackpad_visualizer.py --help
```

### Method 2: Using setup.py

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/biometric-trackpad-auth.git
cd biometric-trackpad-auth
```

2. **Install in development mode:**
```bash
pip3 install -e .
```

This installs the package and creates command-line shortcuts:
- `trackpad-train` → `realtime_trainer.py`
- `trackpad-verify` → `realtime_verify.py`
- `trackpad-visualize` → `trackpad_visualizer.py`

### Method 3: Using Virtual Environment (Recommended for Development)

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/biometric-trackpad-auth.git
cd biometric-trackpad-auth
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the software:**
```bash
python3 realtime_trainer.py --help
```

## Device Permissions

### Option 1: Add User to Input Group (Recommended)

```bash
sudo usermod -a -G input $USER
```

Then log out and log back in for changes to take effect.

### Option 2: Temporary Permission (For Testing)

```bash
sudo chmod 666 /dev/input/event*
```

⚠️ This needs to be run after each reboot.

### Option 3: Create udev Rule (Permanent)

Create a file `/etc/udev/rules.d/99-input.rules`:
```bash
sudo nano /etc/udev/rules.d/99-input.rules
```

Add this line:
```
KERNEL=="event*", SUBSYSTEM=="input", MODE="0666"
```

Reload udev rules:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Finding Your Trackpad Device

Run the device listing command:
```bash
python3 trackpad_visualizer.py --list-devices
```

Look for your trackpad in the output. Common names include:
- "ELAN Touchpad"
- "SynPS/2 Synaptics TouchPad"
- "ETPS/2 Elantech Touchpad"

Note the device path (e.g., `/dev/input/event14`).

## Verification

Test that everything works:

1. **List devices:**
```bash
python3 trackpad_visualizer.py --list-devices
```

2. **Test visualization:**
```bash
python3 trackpad_visualizer.py --device /dev/input/event14
```
(Replace `event14` with your device)

3. **If you see the visualization window, you're ready to go!**

## Troubleshooting

### "Permission denied" error
- Follow the "Device Permissions" section above
- Make sure you logged out and back in after adding yourself to the input group

### "No module named 'evdev'" error
```bash
pip3 install evdev
```

### "No module named 'pygame'" error
```bash
pip3 install pygame
```

### "Cannot open display" error
- Make sure you're running in a graphical environment (not SSH without X forwarding)
- If using SSH, enable X forwarding: `ssh -X user@host`

### Trackpad not detected
- Try different event numbers (event12, event13, event14, etc.)
- Check if your trackpad is recognized: `cat /proc/bus/input/devices`
- Some trackpads may not be compatible

## Next Steps

Once installed, proceed to the [Quick Start Guide](README.md#-quick-start) in the README.

## Uninstallation

If installed with pip:
```bash
pip3 uninstall biometric-trackpad-auth
```

If installed in development mode:
```bash
pip3 uninstall biometric-trackpad-auth
```

To remove all files:
```bash
cd ..
rm -rf biometric-trackpad-auth
```

## Getting Help

If you encounter issues:
1. Check the [Troubleshooting section](README.md#-troubleshooting) in README
2. Search existing [GitHub Issues](https://github.com/yourusername/biometric-trackpad-auth/issues)
3. Create a new issue with details about your problem
