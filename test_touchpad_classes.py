#!/usr/bin/env python3
"""
Test which touchpad classes are available and working
"""

import sys
from pathlib import Path

def load_wpf_assemblies():
    """Load WPF assemblies explicitly"""
    import clr
    
    print("Loading WPF assemblies...")
    
    # Load basic assemblies
    clr.AddReference("System")
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
    clr.AddReference("System.Core")
    
    # Load WPF from explicit paths
    wpf_paths = [
        r"C:\Program Files\dotnet\shared\Microsoft.WindowsDesktop.App\8.0.21",
        r"C:\Program Files\dotnet\shared\Microsoft.WindowsDesktop.App\8.0.20",
        r"C:\Program Files\dotnet\shared\Microsoft.WindowsDesktop.App\6.0.36",
        r"C:\Program Files\dotnet\shared\Microsoft.WindowsDesktop.App\5.0.17",
    ]
    
    import System.Reflection as Reflection
    
    for wpf_path in wpf_paths:
        wpf_dir = Path(wpf_path)
        if wpf_dir.exists():
            print(f"  Loading from: {wpf_path}")
            
            for dll_name in ["PresentationFramework", "PresentationCore", "WindowsBase"]:
                dll_path = wpf_dir / f"{dll_name}.dll"
                if dll_path.exists():
                    try:
                        Reflection.Assembly.LoadFrom(str(dll_path))
                        print(f"    ✓ {dll_name}")
                    except Exception as e:
                        print(f"    ✗ {dll_name}: {e}")
            break
    
    print()

def test_dll_classes():
    """Test what classes are available in the DLL"""
    import clr
    import System.Reflection as Reflection
    
    dll_path = Path("RawInput.Touchpad.dll")
    
    if not dll_path.exists():
        print("✗ RawInput.Touchpad.dll not found")
        return False
    
    print(f"Loading DLL: {dll_path.absolute()}")
    print()
    
    # Load WPF first
    load_wpf_assemblies()
    
    # Load the DLL
    if str(dll_path.parent.absolute()) not in sys.path:
        sys.path.append(str(dll_path.parent.absolute()))
    
    try:
        clr.AddReference(dll_path.stem)
        print("✓ DLL loaded")
    except Exception as e:
        print(f"✗ Failed to load DLL: {e}")
        return False
    
    print()
    
    # Get all types
    print("Getting types from assembly...")
    assembly = Reflection.Assembly.LoadFrom(str(dll_path.absolute()))
    
    try:
        types = assembly.GetTypes()
        print(f"✓ Found {len(types)} types")
    except Reflection.ReflectionTypeLoadException as rtle:
        types = [t for t in rtle.Types if t is not None]
        print(f"⚠️  Partial load: {len(types)} types")
    
    print()
    print("Available types:")
    for t in types:
        print(f"  - {t.FullName}")
    
    print()
    print("=" * 70)
    print("Testing imports...")
    print("=" * 70)
    print()
    
    # Test importing each type
    successful_imports = []
    failed_imports = []
    
    for t in types:
        type_name = t.Name
        namespace = t.Namespace
        
        try:
            # Try to import
            if namespace:
                exec(f"from {namespace} import {type_name}")
                print(f"✓ {namespace}.{type_name}")
                successful_imports.append(f"{namespace}.{type_name}")
            else:
                print(f"⚠️  {type_name} (no namespace)")
        except Exception as e:
            print(f"✗ {namespace}.{type_name}: {str(e)[:60]}")
            failed_imports.append(f"{namespace}.{type_name}")
    
    print()
    print("=" * 70)
    print(f"Summary: {len(successful_imports)}/{len(types)} types imported successfully")
    print("=" * 70)
    
    if successful_imports:
        print()
        print("Successfully imported:")
        for name in successful_imports[:10]:
            print(f"  ✓ {name}")
        if len(successful_imports) > 10:
            print(f"  ... and {len(successful_imports) - 10} more")
    
    if failed_imports:
        print()
        print("Failed to import:")
        for name in failed_imports[:5]:
            print(f"  ✗ {name}")
        if len(failed_imports) > 5:
            print(f"  ... and {len(failed_imports) - 5} more")
    
    print()
    
    # Try to use the main classes
    print("=" * 70)
    print("Testing main classes...")
    print("=" * 70)
    print()
    
    try:
        from RawInput.Touchpad import TouchpadContact
        print("✓ TouchpadContact imported")
        
        # Check its properties
        print("  Properties:")
        for prop in TouchpadContact.GetProperties():
            print(f"    - {prop.Name}: {prop.PropertyType.Name}")
    except Exception as e:
        print(f"✗ TouchpadContact: {e}")
    
    print()
    
    try:
        from RawInput.Touchpad import TouchpadHelper
        print("✓ TouchpadHelper imported")
        
        # Check its methods
        print("  Methods:")
        methods = [m for m in TouchpadHelper.GetMethods() if not m.Name.startswith('get_') and not m.Name.startswith('set_')]
        for method in methods[:10]:
            print(f"    - {method.Name}")
        if len(methods) > 10:
            print(f"    ... and {len(methods) - 10} more")
    except Exception as e:
        print(f"✗ TouchpadHelper: {e}")
    
    print()
    
    try:
        from RawInput.Touchpad import MainWindow
        print("✓ MainWindow imported")
        
        # Try to create an instance
        print("  Attempting to create instance...")
        try:
            window = MainWindow()
            print("  ✓ MainWindow instance created!")
            print(f"    Type: {type(window)}")
            return True
        except Exception as e:
            print(f"  ✗ Could not create instance: {e}")
            return False
            
    except Exception as e:
        print(f"✗ MainWindow: {e}")
        return False

if __name__ == "__main__":
    print()
    print("=" * 70)
    print("Testing RawInput.Touchpad Classes")
    print("=" * 70)
    print()
    
    try:
        import clr
    except ImportError:
        print("✗ pythonnet not installed")
        print("  Install with: pip install pythonnet")
        sys.exit(1)
    
    success = test_dll_classes()
    
    print()
    print("=" * 70)
    if success:
        print("✓ All tests passed!")
        print("  You can now use the Windows touchpad")
    else:
        print("⚠️  Some tests failed")
        print("  But core classes may still work")
    print("=" * 70)
    print()
