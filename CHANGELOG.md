# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
