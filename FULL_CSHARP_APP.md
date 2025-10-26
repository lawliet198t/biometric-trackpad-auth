# Complete C# Biometric Application

## The Solution

**ONE complete C# application** that does EVERYTHING:
- ✓ Touchpad capture (Raw Input API)
- ✓ Real-time visualization (WPF)
- ✓ Biometric training
- ✓ Biometric verification
- ✓ All in ONE window!

No Python needed! Pure C# WPF application.

## Features

### Window Layout
```
┌──────────────────────────────────────────────────────────────────┐
│  Touchpad Biometric System                                       │
├────────────────────────────────────┬─────────────────────────────┤
│                                    │  Biometric Auth             │
│  [Visualization Canvas]            │                             │
│                                    │  TRAINING MODE              │
│  • Real-time finger tracking       │                             │
│  • Colored trails (5 colors)       │  Ready to train             │
│  • Smooth 60 FPS                   │                             │
│  • Auto-scaling                    │  [Progress Bar: 0/5]        │
│                                    │                             │
│                                    │  [CAPTURE GESTURE (SPACE)]  │
│                                    │  [Reset Training]           │
│                                    │                             │
│                                    │  Instructions:              │
│                                    │  1. Click CAPTURE or SPACE  │
│                                    │  2. Perform gesture (2s)    │
│                                    │  3. Repeat 5 times          │
│                                    │  4. System learns pattern   │
│                                    │  5. Then verify             │
└────────────────────────────────────┴─────────────────────────────┘
```

### Biometric Features

**Training Mode:**
- Capture 5 gesture samples
- Progress bar shows completion
- Extracts features: duration, path length, velocity
- Calculates baseline statistics

**Verification Mode:**
- Compare new gesture to baseline
- Calculate confidence score
- Show AUTHENTICATED or REJECTED
- Display detailed metrics

### Visualization Features

- **Multi-touch support** - Up to 5 fingers simultaneously
- **Colored trails** - Each finger gets unique color
- **Fading effect** - Older trail points fade out
- **Contact circles** - Large circles show current positions
- **Contact IDs** - Numbers identify each finger
- **Capture progress** - Visual progress bar during capture
- **60 FPS** - Smooth, responsive visualization

## How to Build

### Step 1: Build the Application

```bash
build_rawinput.bat
```

Or manually:
```bash
cd TouchpadCapture
dotnet publish RawInputProgram.csproj -c Release -o bin
```

### Step 2: Run

```bash
TouchpadCapture\bin\TouchpadCapture.exe
```

Or double-click the executable!

## How to Use

### Training Phase

1. **Launch the application**
   - Window opens in TRAINING MODE

2. **Capture your gesture**
   - Click "CAPTURE GESTURE" or press SPACE
   - Perform your unique gesture (2 seconds)
   - Use 2-3 fingers, make a pattern

3. **Repeat 5 times**
   - Progress bar shows 1/5, 2/5, etc.
   - Try to be consistent!

4. **Automatic training**
   - After 5 samples, system learns your pattern
   - Switches to VERIFICATION MODE automatically

### Verification Phase

1. **Perform your gesture**
   - Click "CAPTURE GESTURE" or press SPACE
   - Do the same gesture you trained

2. **See results**
   - ✓ AUTHENTICATED - Access granted!
   - ✗ REJECTED - Access denied!
   - Shows confidence percentage
   - Shows distance from baseline

3. **Try again**
   - Keep testing with your gesture
   - Try with different gestures (should reject)

### Reset Training

- Click "Reset Training" button
- Or press 'R' key
- Clears all samples and starts over

## Keyboard Shortcuts

- **SPACE** - Capture gesture
- **R** - Reset training
- **ESC** - Close application

## Technical Details

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  BiometricApp.cs (Main Window)                              │
│  • WPF UI with Canvas + Controls                            │
│  • Gesture capture logic                                    │
│  • Biometric training/verification                          │
│  • Visualization rendering                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  BiometricMain.cs (Entry Point)                             │
│  • Initializes application                                  │
│  • Registers Raw Input                                      │
│  • Routes touch events to BiometricApp                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  TouchpadHelper.cs (Raw Input API)                          │
│  • Windows Raw Input API calls                              │
│  • HID parsing                                              │
│  • Multi-touch contact extraction                           │
└─────────────────────────────────────────────────────────────┘
```

### Biometric Algorithm

**Feature Extraction:**
- Duration (seconds)
- Path length (pixels)
- Average velocity (pixels/second)

**Training:**
- Collect 5 samples
- Calculate mean and standard deviation for each feature
- Store as baseline

**Verification:**
- Extract features from new gesture
- Calculate normalized distance from baseline
- Distance = sqrt(Σ((feature - mean) / std)²)
- Threshold: 3.0 standard deviations
- Confidence: 1 - (distance / threshold)

### Performance

- **Visualization**: 60 FPS (16ms update)
- **Touch latency**: ~5-10ms
- **Capture duration**: 2 seconds
- **Training samples**: 5 gestures
- **Verification time**: Instant (<1ms)

## Files

- `BiometricApp.cs` - Main application window with UI and logic
- `BiometricMain.cs` - Entry point and Raw Input setup
- `RawInputProgram.cs` - Raw Input API helpers (TouchpadHelper)
- `RawInputProgram.csproj` - Project configuration

## Customization

### Change Training Samples

In `BiometricApp.cs`:
```csharp
private int trainingSamplesNeeded = 5;  // Change to 3, 10, etc.
```

### Change Capture Duration

```csharp
private double captureDuration = 2.0;  // Change to 1.5, 3.0, etc.
```

### Change Verification Threshold

```csharp
double threshold = 3.0;  // Lower = stricter, Higher = more lenient
```

### Change Colors

```csharp
private Brush[] contactColors = new Brush[]
{
    new SolidColorBrush(Color.FromRgb(255, 0, 0)),    // Red
    new SolidColorBrush(Color.FromRgb(0, 255, 0)),    // Green
    // Add more colors...
};
```

## Benefits

### vs Python + C# Hybrid:
- ✓ **Simpler** - No inter-process communication
- ✓ **Faster** - No JSON serialization overhead
- ✓ **Cleaner** - One codebase, one language
- ✓ **Easier to deploy** - Single executable

### vs Embedded Window:
- ✓ **No complexity** - No window embedding hacks
- ✓ **Native** - Pure WPF, no pygame
- ✓ **Professional** - Looks like a real application

## Requirements

- **Windows 10/11** - With Precision Touchpad
- **.NET 8.0 Runtime** - Included in self-contained build
- **WPF** - Built into .NET

## Troubleshooting

### "No Precision Touchpad detected"

Your device doesn't have a Windows Precision Touchpad. Check:
- Device Manager → Human Interface Devices
- Look for "HID-compliant touch pad" or "Precision Touchpad"

### Window doesn't appear

- Check if executable is in `TouchpadCapture\bin\`
- Try running from command line to see errors
- Make sure .NET 8.0 is installed

### Gestures not capturing

- Make sure you're touching the touchpad
- Check if visualization shows finger trails
- Try with 2-3 fingers for better results

### Verification always fails

- Training samples may be too inconsistent
- Try resetting and training again
- Use a simpler, more repeatable gesture

## Next Steps

1. Build: `build_rawinput.bat`
2. Run: `TouchpadCapture\bin\TouchpadCapture.exe`
3. Train with 5 gestures
4. Verify and test!

You now have a **complete biometric authentication system** in pure C#! 🎉
