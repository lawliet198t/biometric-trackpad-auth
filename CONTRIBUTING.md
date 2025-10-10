# Contributing to Biometric Trackpad Authentication System

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (Linux distro, Python version, trackpad model)
- Error messages or logs

### Suggesting Enhancements

Enhancement suggestions are welcome! Please create an issue with:
- Clear description of the enhancement
- Use case and benefits
- Possible implementation approach (if you have ideas)

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add comments for complex logic
   - Update documentation if needed

4. **Test your changes**
   - Ensure existing functionality still works
   - Test on your trackpad device
   - Verify training and verification modes

5. **Commit your changes**
   ```bash
   git commit -m "Add: brief description of changes"
   ```
   Use prefixes: `Add:`, `Fix:`, `Update:`, `Remove:`

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Describe what changes you made and why
   - Reference any related issues
   - Include screenshots/videos if relevant

## Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for classes and functions
- Keep functions focused and modular

### Documentation

- Update README.md if you add new features
- Add inline comments for complex algorithms
- Update docstrings when changing function behavior

### Testing

- Test on actual hardware (trackpad)
- Verify both training and verification modes
- Check edge cases (very fast/slow gestures, etc.)

## Priority Areas for Contribution

We especially welcome contributions in these areas:

1. **Windows Support**
   - Alternative to evdev for Windows
   - Windows input device handling

2. **macOS Support**
   - Testing and fixes for macOS

3. **Stage 2 Verification**
   - CNN-based shape verification
   - Deep learning model integration

4. **Performance Optimization**
   - Faster feature extraction
   - Real-time processing improvements

5. **Documentation**
   - Tutorials and guides
   - Video demonstrations
   - Translation to other languages

6. **Testing**
   - Unit tests
   - Integration tests
   - Different trackpad models

## Questions?

Feel free to open an issue for any questions about contributing!

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help create a welcoming environment

Thank you for contributing! 🎉
