#!/usr/bin/env python3
"""
Test Windows Multi-Touch Setup

This script tests if your Windows multi-touch setup is working correctly.
"""

import sys
from pathlib import Path

def test_pythonnet():
    """Test if pythonnet is installed"""
    print("=" * 70)
    print("Test 1: Python.NET Installation")
    print("=" * 70)
    
    try:
        import clr
        print("✓ pythonnet is installed")
        return True
    except ImportError:
        print("✗ pythonnet is NOT installed")
        print("  Install with: pip install pythonnet")
        return False

def test_dll_exists():
    """Test if the C# DLL exists"""
    print("\n" + "=" * 70)
    print("Test 2: C# DLL File")
    print("=" * 70)
    
    possible_paths = [
        "RawInput.Touchpad.dll",
        "lib/RawInput.Touchpad.dll",
        "bin/RawInput.Touchpad.dll",
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            print(f"✓ Found DLL at: {Path(path).absolute()}")
            return True, path
    
    print("✗ RawInput.Touchpad.dll NOT found")
    print("  Download from: https://github.com/emoacht/RawInput.Touchpad/releases")
    print("  Place it in the same directory as this script")
    return False, None

def test_dll_load(dll_path):
    """Test if the DLL can be loaded"""
    print("\n" + "=" * 70)
    print("Test 3: Load C# DLL")
    print("=" * 70)
    
    try:
        import clr
        dll_abs = str(Path(dll_path).absolute())
        print(f"Loading: {dll_abs}")
        clr.AddReference(dll_abs)
        print("✓ DLL loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to load DLL: {e}")
        return False

def test_import_classes():
    """Test if we can import C# classes"""
    print("\n" + "=" * 70)
    print("Test 4: Import C# Classes")
    print("=" * 70)
    
    try:
        # Try to import the touchpad classes
        from RawInput.Touchpad import TouchpadForm
        print("✓ Successfully imported TouchpadForm")
        return True
    except ImportError as e:
        print(f"⚠️  Could not import TouchpadForm: {e}")
        print("  The DLL structure might be different than expected")
        print("  Listing available types...")
        
        try:
            import clr
            import System
            assembly = clr.System.Reflection.Assembly.LoadFrom("RawInput.Touchpad.dll")
            print("\n  Available types in DLL:")
            for type_info in assembly.GetTypes():
                print(f"    - {type_info.FullName}")
        except Exception as e2:
            print(f"  Could not list types: {e2}")
        
        return False

def test_touchpad_detection():
    """Test if Windows Precision Touchpad is detected"""
    print("\n" + "=" * 70)
    print("Test 5: Windows Precision Touchpad Detection")
    print("=" * 70)
    
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\PrecisionTouchPad",
            0,
            winreg.KEY_READ
        )
        winreg.CloseKey(key)
        print("✓ Windows Precision Touchpad detected in registry")
        return True
    except:
        print("⚠️  Windows Precision Touchpad NOT detected in registry")
        print("  Your touchpad may not support Precision Touchpad API")
        print("  Check: Settings → Devices → Touchpad")
        return False

def test_integration():
    """Test if the Python wrapper works"""
    print("\n" + "=" * 70)
    print("Test 6: Python Integration")
    print("=" * 70)
    
    try:
        from windows_touchpad_pythonnet import WindowsTouchpadPythonNET
        print("✓ Successfully imported WindowsTouchpadPythonNET")
        
        # Try to create instance
        capture = WindowsTouchpadPythonNET()
        print("✓ Successfully created capture instance")
        
        return True
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Windows Multi-Touch Setup Test" + " " * 23 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    results = []
    
    # Test 1: pythonnet
    results.append(("Python.NET", test_pythonnet()))
    
    # Test 2: DLL exists
    dll_exists, dll_path = test_dll_exists()
    results.append(("DLL File", dll_exists))
    
    if dll_exists:
        # Test 3: Load DLL
        dll_loaded = test_dll_load(dll_path)
        results.append(("Load DLL", dll_loaded))
        
        if dll_loaded:
            # Test 4: Import classes
            results.append(("Import Classes", test_import_classes()))
    
    # Test 5: Touchpad detection
    results.append(("Touchpad Detection", test_touchpad_detection()))
    
    # Test 6: Integration
    if dll_exists:
        results.append(("Python Integration", test_integration()))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("   Your Windows multi-touch setup is ready!")
        print("   Run: python realtime_trainer.py")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("   See above for details and follow the instructions")
        print("   Refer to: SETUP_WINDOWS_MULTITOUCH.md")
    print("=" * 70)
    print()
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
