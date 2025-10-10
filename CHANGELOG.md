# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
