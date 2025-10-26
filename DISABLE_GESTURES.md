# Disable Windows Touchpad Gestures

## The Problem

While capturing biometric gestures, Windows interprets multi-finger touches as system gestures:
- 3-finger swipe → Switch apps
- 4-finger swipe → Show desktop
- Pinch → Zoom
- etc.

This interferes with your biometric capture!

## Solution: Disable Windows Gestures

### Method 1: Windows Settings (Recommended)

1. Open **Windows Settings** (Win + I)
2. Go to **Devices** → **Touchpad**
3. Scroll down to **Three-finger gestures**
4. Set all to **"Nothing"**:
   - Swipes: Nothing
   - Taps: Nothing
5. Scroll to **Four-finger gestures**
6. Set all to **"Nothing"**:
   - Swipes: Nothing
   - Taps: Nothing

### Method 2: Registry (Advanced)

Run this in PowerShell as Administrator:

```powershell
# Disable 3-finger gestures
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\PrecisionTouchpad" -Name "ThreeFingerTapEnabled" -Value 0
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\PrecisionTouchpad" -Name "ThreeFingerSlideEnabled" -Value 0

# Disable 4-finger gestures
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\PrecisionTouchpad" -Name "FourFingerTapEnabled" -Value 0
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\PrecisionTouchpad" -Name "FourFingerSlideEnabled" -Value 0

# Restart Explorer
Stop-Process -Name explorer -Force
```

### Method 3: Group Policy (Enterprise)

1. Run `gpedit.msc`
2. Navigate to: Computer Configuration → Administrative Templates → Windows Components → Edge Swipe
3. Enable "Disable Edge Swipe"

## Quick Check

After disabling, test:
1. Swipe with 3 fingers → Nothing should happen
2. Swipe with 4 fingers → Nothing should happen
3. Pinch → Nothing should happen

## Re-enable After Capture

To re-enable gestures after biometric capture:
1. Go back to Settings → Devices → Touchpad
2. Set gestures back to your preferred actions

## Alternative: Capture Mode

You could also create a "Capture Mode" that temporarily disables gestures programmatically, but this requires admin privileges and is more complex.

## Summary

✓ **Disable 3-finger gestures**: Set to "Nothing"
✓ **Disable 4-finger gestures**: Set to "Nothing"
✓ **Test**: Swipe should do nothing
✓ **Capture**: Now you can capture multi-finger gestures!

This is a **one-time setup** - you only need to do it once before using the biometric system.
