# Biometric Trackpad Authentication System

A pure motion dynamics biometric authentication system using trackpad gestures. Works with ELAN trackpads providing only (X, Y, Timestamp) data - no pressure or contact area needed!

✨ **Cross-Platform Support**: Works on **Linux** and **Windows**! Automatically detects your platform and uses the appropriate backend.

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-blue.svg)

## 🎯 Features

- **Cross-Platform Support** 🆕
  - **Linux**: evdev backend for multi-touch trackpads
  - **Windows**: Windows Precision Touchpad API
  - Automatic platform detection
  - No platform-specific code needed!

- **Automatic Trackpad Detection**
  - Automatically finds your trackpad device
  - No manual device path configuration needed
  - Intelligent scoring based on capabilities
  - Fallback to manual specification if needed (Linux)

- **Advanced Biometric Feature Extraction**
  - Velocity, Acceleration, Jerk (smoothness)
  - Curvature analysis (path shape)
  - Hesitation detection (micro-pauses)
  - Duration and path metrics

- **Multi-Stage Verification**
  - Stage 1: Gatekeeper (duration, path length)
  - Stage 2: Shape verification (future: CNN)
  - Stage 3: Dynamics verification (velocity, jerk, hesitations)

- **Real-Time Visualization**
  - Live metrics display while drawing
  - Instant verification feedback
  - Multi-touch gesture tracking

- **Training Mode**
  - Learn your unique biometric baseline
  - Adaptive verification thresholds
  - Automatic baseline saving

## 📋 Requirements

### Platform
- **Linux** (Ubuntu, Debian, Fedora, Arch, etc.)
- **Windows** (10/11 with Precision Touchpad)
- macOS support coming soon

### Software
- Python 3.7+
- **Linux**: Multi-touch trackpad (ELAN, Synaptics, etc.)
- **Windows**: Windows Precision Touchpad

### Python Packages
The system automatically installs the correct packages for your platform:

```bash
pip install -r requirements.txt
```

**Platform-specific dependencies:**
- **Linux**: `evdev` (for input device access)
- **Windows**: `pywin32` (for Windows Touch API)
- **All platforms**: `numpy`, `pygame`

## 🚀 Quick Start

### 1. Setup Environment

Install dependencies:

**Linux/macOS:**
```bash
# Option 1: Use virtual environment (recommended)
./setup_venv.sh
source venv/bin/activate

# Option 2: System-wide install (if allowed)
pip3 install -r requirements.txt
```

**Windows:**
```cmd
REM Option 1: Use virtual environment (recommended)
setup_venv.bat
venv\Scripts\activate.bat

REM Option 2: System-wide install
pip install -r requirements.txt
```

### 2. Detect Your Trackpad (Optional)

The system now **automatically detects** your trackpad! To verify detection:
```bash
python3 detect_trackpad.py
```

This will show:
- Auto-detected trackpad device
- All available trackpad devices
- Device scores and capabilities

### 3. Train Your Baseline

Collect 10 training samples of your gesture (trackpad auto-detected):
```bash
python3 realtime_trainer.py --samples 10
```

Or specify device manually:
```bash
python3 realtime_trainer.py --device /dev/input/event14 --samples 10
```

**Instructions:**
- Draw your gesture consistently (same shape, speed, style)
- Press `SPACE` after each gesture
- Baseline will be learned automatically after 10 samples
- Saves to `baseline.pkl`

### 4. Verify Gestures

Use your trained baseline to verify new gestures (trackpad auto-detected):
```bash
python3 realtime_verify.py --baseline baseline.pkl
```

Or specify device manually:
```bash
python3 realtime_verify.py --baseline baseline.pkl --device /dev/input/event14
```

**Features:**
- Real-time metrics update as you draw
- Live verification scores
- Instant pass/fail feedback

## 📁 Project Structure

```
.
├── advanced_biometrics.py           # Core biometric feature extraction
├── realtime_trainer.py   # Training mode
├── realtime_verify.py # Verification mode with live display
├── trackpad_lib.py                 # Cross-platform trackpad capture library
├── windows_touchpad.py             # Windows Precision Touchpad backend
├── trackpad_visualizer.py          # Complete gesture visualizer
├── detect_trackpad.py              # Cross-platform trackpad detection utility
├── setup_venv.sh                   # Virtual environment setup script (Linux/macOS)
├── requirements.txt                # Platform-aware Python dependencies
└── README.md                       # This file
```

### File Descriptions

**`advanced_biometrics.py`**
- Core biometric feature extraction and verification logic
- `AdvancedFeatureExtractor`: Extract velocity, acceleration, jerk, curvature
- `BiometricBaseline`: Learn and store baseline from training samples
- `MultiStageVerifier`: Multi-stage verification with strict gating

**`realtime_trainer.py`**
- Training mode - collect samples and learn baseline
- Collects N training samples
- Learns biometric baseline automatically
- Saves baseline to `baseline.pkl`

**`realtime_verify.py`**
- Verification mode - load baseline and verify gestures
- Shows real-time metrics while drawing
- Live verification scores (Stage 1, Stage 3, Overall)
- Instant pass/fail feedback

**`trackpad_lib.py`**
- Cross-platform trackpad capture and visualization library
- `TrackpadCapture`: Handle device input and gesture tracking (Linux/Windows)
- `GestureVisualizer`: Pygame visualization
- `detect_trackpad()`: Automatic trackpad detection (cross-platform)
- `list_all_trackpads()`: List all available trackpad devices
- Multi-touch support
- Automatic platform detection and backend selection

**`windows_touchpad.py`**
- Windows Precision Touchpad backend
- `WindowsTouchpadCapture`: Windows Touch API integration
- Compatible interface with Linux backend
- Multi-touch gesture support via Windows Touch API

**`detect_trackpad.py`**
- Cross-platform trackpad detection utility
- Shows all detected trackpad devices
- Displays device capabilities and scores
- Provides usage examples for your platform

**`trackpad_visualizer.py`**
- Complete trackpad gesture visualizer with feature extraction
- Multi-touch gesture capture
- Feature extraction (25-element vector)
- Export to JSON

## 💡 Usage Examples

### Detect Trackpad
```bash
python3 detect_trackpad.py
```

### Basic Training (10 samples, auto-detect)
```bash
python3 realtime_trainer.py --samples 10
```

### Extended Training (20 samples for better accuracy)
```bash
python3 realtime_trainer.py --samples 20
```

### Verify with Saved Baseline (auto-detect)
```bash
python3 realtime_verify.py --baseline baseline.pkl
```

### Manual Device Specification
```bash
# If auto-detection fails, specify device manually
python3 realtime_trainer.py --device /dev/input/event14 --samples 10
python3 realtime_verify.py --baseline baseline.pkl --device /dev/input/event14
```

### Visualize and Export Gestures
```bash
python3 trackpad_visualizer.py --device /dev/input/event14
```

### Training Mode with Export
```bash
python3 trackpad_visualizer.py --device /dev/input/event14 --training --samples 50
```

## ⌨️ Keyboard Controls

| Key | Action |
|-----|--------|
| `SPACE` | Start/stop capture (or capture single gesture) |
| `C` | Clear current gestures |
| `Q` / `ESC` | Quit application |
| `S` | Save/export gestures (in visualizer mode) |

## 📊 Understanding the Metrics

### Duration
How long you take to draw the gesture. Very important for verification! Your baseline will learn your typical duration.

### Velocity CV (Coefficient of Variation)
Measures consistency of your drawing speed.
- Lower = more consistent speed
- Higher = more speed variations

### Jerk CV ⭐ **CRITICAL**
Measures smoothness of motion (rate of change of acceleration).
- Lower = smooth, practiced motion (authentic)
- Higher = conscious tracing (potential forgery)
- **This is the most important metric for detecting forgeries!**

### Hesitations
Number of micro-pauses during drawing. Your baseline learns your typical hesitation pattern. Forgers often have different hesitation patterns.

### Path Length
Total distance traveled while drawing. Should be consistent for the same gesture.

### Verification Scores
- **Stage 1 (Gatekeeper)**: Duration and path length checks
- **Stage 3 (Dynamics)**: Velocity, jerk, and hesitation checks
- **Overall**: Weighted combination (Stage 1: 30%, Stage 3: 70%)
- **Pass threshold**: 70%

## 🔧 Troubleshooting

### Gestures are being skipped
- Draw slower (keep finger on trackpad longer)
- Draw a longer path
- Check minimum requirements (5 points, 0.05s duration)
- Use `trackpad_visualizer.py` to see what's being captured

### Verification always fails
- Retrain with more samples (`--samples 20`)
- Draw more consistently during training
- Check that you're drawing the same gesture
- Verify your gesture meets minimum requirements

### Can't find trackpad device
- Run: `python3 detect_trackpad.py` to see auto-detection results
- The system automatically detects trackpads with multi-touch support
- If auto-detection fails, manually specify: `--device /dev/input/eventX`
- Check permissions: `sudo chmod 666 /dev/input/event*`
- Add yourself to input group: `sudo usermod -a -G input $USER` (then log out/in)

### Permission denied on device (Linux)
- Add yourself to input group: `sudo usermod -a -G input $USER`
- Log out and log back in
- Or run with sudo (not recommended)

### Windows multi-touch setup
**For TRUE multi-touch on Windows:**

The pre-built releases only have an EXE (not DLL). You need to either:
1. **Build from source** (requires .NET SDK) - See [`README_WINDOWS_TOUCHPAD.md`](README_WINDOWS_TOUCHPAD.md)
2. **Use Linux** (easiest - works out of the box!)

Current Windows version uses mouse simulation (single-point only).

### Real-time metrics not updating
- Draw more points (draw slower or longer path)
- Need at least 10 points for real-time verification
- Check that capture is active (status shows "CAPTURING")

## 🎨 Gesture Requirements

For best results, your gesture should:

**Duration:**
- Minimum: 0.05 seconds
- Maximum: 10 seconds
- Recommended: 0.5 - 3 seconds

**Points:**
- Minimum: 5 points
- Recommended: 20+ points (draw slower for more points)

**Consistency:**
- Draw the same shape each time
- Use similar speed and rhythm
- Keep the same drawing style (smooth vs. jerky)

**Tips:**
- Practice your gesture a few times before training
- Draw at a comfortable, natural speed
- Don't rush - slower is better for capturing details
- Keep your finger on the trackpad throughout the gesture

## 🔬 How It Works

### Training Phase
1. You draw your gesture N times (default: 10)
2. System extracts biometric features from each sample
3. Calculates mean and standard deviation for each feature
4. Saves baseline to `baseline.pkl`

### Verification Phase
1. You draw your gesture
2. System extracts biometric features
3. **Stage 1 (Gatekeeper)**: Checks duration and path length
   - Must be within 2σ of baseline
   - Fast rejection of obvious forgeries
4. **Stage 3 (Dynamics)**: Checks velocity, jerk, hesitations
   - Compares patterns to baseline
   - Jerk analysis is critical for detecting forgeries
5. Overall score calculated (weighted combination)
6. Pass if score >= 70%

### Key Insight
**Jerk (rate of change of acceleration) is the most important metric!**
- Authentic gestures: smooth, practiced motion → low jerk variation
- Forgeries: conscious tracing → high jerk variation

## 🧬 Biometric Features

### Spatial Features
- Velocity: Speed of drawing (pixels/second)
- Acceleration: Rate of change of velocity
- Jerk: Rate of change of acceleration (smoothness)
- Curvature: Direction changes in path
- Path length: Total distance traveled
- Bounding box: Spatial extent of gesture

### Temporal Features
- Duration: Total time to draw
- Rhythm: Timing patterns between points
- Hesitations: Micro-pauses during drawing

### Behavioral Features
- Velocity patterns: How speed changes over time
- Acceleration patterns: How acceleration changes
- Jerk patterns: Smoothness consistency
- Hesitation patterns: Where and when you pause

## 🔒 Security Considerations

### Strengths
✅ Jerk analysis makes forgery very difficult  
✅ Multi-stage verification with strict gating  
✅ Adaptive thresholds based on your baseline  
✅ No pressure data needed (works with basic trackpads)

### Limitations
⚠️ Requires consistent gesture execution  
⚠️ May fail if you're tired, stressed, or injured  
⚠️ Environmental factors (cold hands, wet fingers) may affect  
⚠️ Not suitable for high-security applications (yet)

### Recommendations
- Use as secondary authentication factor
- Retrain baseline periodically
- Collect more training samples for better accuracy
- Practice your gesture before training

## 🛠️ Technical Details

### Automatic Trackpad Detection

**Linux:**
1. Scans all `/dev/input/event*` devices
2. Checks for multi-touch capabilities:
   - `ABS_MT_POSITION_X` and `ABS_MT_POSITION_Y` (position tracking)
   - `ABS_MT_SLOT` (multi-finger support)
   - `ABS_MT_TRACKING_ID` (finger identification)
3. Scores devices based on:
   - Device name keywords (trackpad, touchpad, synaptics, elan, etc.)
   - Number of capabilities
4. Selects the highest-scoring device

**Windows:**
1. Checks for Windows Precision Touchpad support
2. Uses Windows Touch API for multi-touch input
3. Automatically enabled if touchpad is detected

**Supported trackpad types:**
- **Linux**: ELAN, Synaptics, ALPS, Apple BCM5974, PS/2, any multi-touch evdev device
- **Windows**: Windows Precision Touchpad (most modern laptops)

### Hardware Requirements
- **Linux**: Multi-touch trackpad with evdev support (ELAN, Synaptics, or compatible)
- **Windows**: Windows Precision Touchpad (most modern laptops)
- Multi-touch capability (2+ fingers)

### Data Captured
- X, Y coordinates (absolute position)
- Timestamp (monotonic, nanosecond precision)
- No pressure or contact area needed!

### Feature Vector
- 25-element normalized vector (0-1 range)
- Spatial features (10): path, curvature, position
- Temporal features (10): duration, velocity, acceleration, rhythm
- Multi-finger features (5): coordination, spacing

### Verification Algorithm
- Stage 1: Invariant checks (duration, path length)
- Stage 2: Shape verification (future: CNN)
- Stage 3: Dynamics verification (velocity, jerk, hesitations)
- Scoring: Weighted combination with sigma-based thresholds

## 🚧 Future Enhancements

- [ ] Stage 2 CNN-based shape verification
- [ ] Multi-gesture authentication
- [ ] Continuous authentication
- [ ] Adaptive baseline updates
- [ ] Windows support (alternative to evdev)
- [ ] macOS support
- [ ] Mobile device support
- [ ] Web interface

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This is a research prototype for biometric authentication using trackpad gesture dynamics. Use at your own risk. Not recommended for high-security applications without further testing and validation.

## 🙏 Acknowledgments

Key Technologies:
- Python 3
- NumPy (numerical computing)
- Pygame (visualization)
- evdev (Linux input device interface)

## 📧 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your device path is correct
3. Ensure you have required permissions
4. Try with different gesture (simpler or more complex)

For best results:
- Practice your gesture before training
- Draw consistently during training
- Use natural, comfortable gestures
- Retrain if verification accuracy drops

---

**Made with ❤️ for biometric security research**
# biometric-trackpad-auth
