# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security & Reliability Updates 🔒
- **Security Upgrade: JSON Baselines**
  - Switched from insecure `pickle` serialization to standard `JSON`
  - Prevents arbitrary code execution vulnerabilities
  - **Breaking Change**: Old `.pkl` baselines are no longer supported. Please retrain.

- **Fixed: Windows Visualization Bug**
  - Fixed issue where lines wouldn't draw immediately on some systems
  - Implemented safe default coordinate ranges while auto-detection runs
  - Ensures immediate visual feedback during training/verification

- **Fixed: Data Loss on High-Frequency Inputs**
  - Increased input buffer size (10 -> 200 frames)
  - Prevents gaps/stuttering in lines during micro-lags
  - Improved tracking accuracy for fast gestures

- **Fixed: Biometric Math**
  - Corrected "Jerk" calculation time-alignment
  - Improved accuracy of smoothness metrics

### Added - Adaptive Window Sizing 🎯
- **Auto-detection of touchpad dimensions**
  - Automatically detects coordinate ranges from touchpad
  - Calculates optimal window size based on touchpad aspect ratio
  - Works across different touchpad models and sizes
  - `test_touchpad_dimensions.py`: Test script to verify detection

- **Adaptive visualization**
  - Window automatically matches touchpad proportions
  - Better 1:1 mapping between touchpad and screen
  - Improved gesture visualization accuracy
  - Enabled by default in training and verification programs

### Fixed - Multi-Finger Tracking 🖐️
- **Removed JSON output throttling in C# exe**
  - Eliminated frame skipping during multi-finger gestures
  - Immediate data output for smooth tracking
  - ~1000 FPS data rate (was ~60 FPS)

- **Added coordinate normalization**
  - Raw touchpad coordinates now properly normalized to screen space
  - Multi-finger gestures display correctly in visualization
  - Dynamic range detection from Windows backend
  - `rebuild_touchpad.bat`: Script to rebuild exe with fixes

### Current State - Windows Raw Input Implementation 🎉

- **Core Implementation**
  - `simple_windows_touchpad.py`: Minimal, high-performance touchpad reader
  - Direct Raw Input API access via C# subprocess
  - Timeout-based finger lift detection (15ms default)
  - Threading for non-blocking reads with small queue for low latency
  - Support for orjson for faster JSON parsing
  - 1000 FPS polling for maximum performance
  - Multi-touch contact tracking with unique ContactId per finger

- **Biometric Training & Verification**
  - `realtime_trainer.py`: Interactive training with pygame visualization
  - `realtime_verify.py`: Real-time verification with live metrics
  - Multi-stage verification system (Gatekeeper + Dynamics)
  - Advanced feature extraction (velocity, jerk, curvature, hesitation)
  - Baseline saved to `baseline.pkl`
  - Visual feedback during gesture capture

- **One-Command Setup**
  - `setup_windows.bat`: Complete automated setup script
  - Checks for .NET SDK and Python
  - Creates virtual environment automatically
  - Installs all dependencies
  - Builds TouchpadCapture.exe
  - All-in-one solution for Windows users

- **TouchpadCapture C# Program**
  - Raw Input API wrapper using RawInput.Touchpad
  - Outputs JSON contact data to stdout
  - Self-contained build with all dependencies
  - High-precision coordinate data (0-65535 range)
  - Millisecond-precision timestamps

- **Documentation**
  - README with clear Quick Start section
  - QUICKSTART.md for 5-minute setup guide
  - INSTALL.md with quick and manual installation
  - CONTRIBUTING.md for development guidelines
  - DEMO.md for demonstration scenarios
  - DISABLE_GESTURES.md for Windows gesture configuration

### Changed
- Simplified to Windows-only implementation (removed Linux evdev code)
- Focused on Raw Input API for true multi-touch support
- Streamlined file structure with essential files only
- Updated all documentation to reflect current implementation

### Improved
- Setup process reduced to one command
- Better performance with threading and optimized polling
- Clear separation of essential vs optional files
- Comprehensive error messages with solutions
- Real-time visual feedback during training and verification

## [Previous Unreleased]

### Added - Cross-Platform Support 🎉
- **Windows Support**
  - `windows_touchpad.py`: Windows Precision Touchpad backend
  - Windows Touch API integration for multi-touch input
  - Automatic Windows platform detection
  - Compatible interface with Linux backend
  - Support for Windows 10/11 Precision Touchpads

- **Automatic Platform Detection**
  - Detects Linux, Windows, or macOS automatically
  - Loads appropriate backend based on platform
  - No platform-specific code needed in user scripts
  - Seamless cross-platform experience

- **Automatic Trackpad Detection**
  - `detect_trackpad()` function for automatic device detection (cross-platform)
  - `list_all_trackpads()` function to list all available trackpad devices
  - Linux: Intelligent scoring based on device capabilities and name matching
  - Windows: Windows Precision Touchpad detection
  - Support for multiple trackpad types (ELAN, Synaptics, ALPS, BCM5974, PS/2)
  - `detect_trackpad.py` utility script for testing detection (cross-platform)
  - `test_detection.py` test suite for validation
  - `setup_venv.sh` script for easy virtual environment setup

### Changed
- **Platform-Aware Dependencies**
  - `requirements.txt` now uses platform markers
  - `evdev` only installed on Linux
  - `pywin32` only installed on Windows
  - Automatic dependency resolution based on platform

- **Cross-Platform TrackpadCapture**
  - `TrackpadCapture` now works on Linux and Windows
  - Automatic backend selection based on platform
  - Auto-detects trackpad by default (device_path optional on Linux)
  - Unified API across platforms

- **Updated Scripts**
  - `realtime_trainer.py` now works on Windows
  - `realtime_verify.py` now works on Windows
  - All scripts automatically detect platform
  - Updated README with cross-platform documentation

### Improved
- No more manual device path configuration needed
- No more platform-specific code in user scripts
- Better user experience for first-time setup on any platform
- Clearer error messages with helpful suggestions
- Comprehensive device detection with fallback options
- Windows users can now use the system without Linux VM!

### Planned
- Stage 2 CNN-based shape verification
- Windows support (alternative to evdev)
- macOS support
- Multi-gesture authentication
- Continuous authentication
- Adaptive baseline updates
- Mobile device support
- Web interface

## [0.1.0] - 2025-01-10

### Added
- Initial release
- Advanced biometric feature extraction (velocity, acceleration, jerk, curvature)
- Multi-stage verification system (Stage 1: Gatekeeper, Stage 3: Dynamics)
- Real-time visualization with pygame
- Training mode for baseline learning
- Verification mode with live metrics display
- Multi-touch gesture tracking
- Hesitation detection
- 25-element normalized feature vector
- JSON export functionality
- Comprehensive documentation

### Features
- Pure motion dynamics approach (X, Y, Timestamp only)
- No pressure or contact area required
- Adaptive verification thresholds
- Automatic baseline saving
- Real-time metrics update while drawing
- Instant pass/fail feedback

### Platform Support
- Linux (Ubuntu, Debian, Fedora, Arch)
- ELAN trackpad support
- evdev interface

### Known Limitations
- Linux only (Windows and macOS not supported)
- Requires consistent gesture execution
- May be affected by environmental factors
- Not suitable for high-security applications without further validation

### Documentation
- Comprehensive README with quick start guide
- Installation guide (INSTALL.md)
- Contributing guidelines (CONTRIBUTING.md)
- MIT License
- Troubleshooting section
- Usage examples

[Unreleased]: https://github.com/yourusername/biometric-trackpad-auth/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/biometric-trackpad-auth/releases/tag/v0.1.0
