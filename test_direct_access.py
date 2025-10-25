#!/usr/bin/env python3
"""
Test direct access to C# types without importing
"""

import sys
from pathlib import Path

def test_direct_access():
    """Access C# types directly through the assembly"""
    import clr
    import System.Reflection as Reflection
    
    # Load WPF assemblies
    print("Loading WPF assemblies...")
    wpf_path = r"C:\Program Files\dotnet\shared\Microsoft.WindowsDesktop.App\8.0.21"
    for dll_name in ["PresentationFramework", "PresentationCore", "WindowsBase"]:
        dll = Path(wpf_path) / f"{dll_name}.dll"
        if dll.exists():
            Reflection.Assembly.LoadFrom(str(dll))
            print(f"  ✓ {dll_name}")
    
    print()
    
    # Load basic assemblies
    clr.AddReference("System")
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
    clr.AddReference("System.Core")
    
    # Load the touchpad DLL
    dll_path = Path("RawInput.Touchpad.dll")
    if not dll_path.exists():
        print("✗ RawInput.Touchpad.dll not found")
        return False
    
    print(f"Loading: {dll_path.absolute()}")
    assembly = Reflection.Assembly.LoadFrom(str(dll_path.absolute()))
    print("✓ Assembly loaded")
    print()
    
    # Get types
    try:
        types = assembly.GetTypes()
    except Reflection.ReflectionTypeLoadException as rtle:
        types = [t for t in rtle.Types if t is not None]
    
    print(f"Found {len(types)} types")
    print()
    
    # Find the types we need
    TouchpadContact = None
    TouchpadHelper = None
    MainWindow = None
    App = None
    
    for t in types:
        name = t.Name
        if name == "TouchpadContact":
            TouchpadContact = t
            print(f"✓ Found TouchpadContact")
        elif name == "TouchpadHelper":
            TouchpadHelper = t
            print(f"✓ Found TouchpadHelper")
        elif name == "MainWindow":
            MainWindow = t
            print(f"✓ Found MainWindow")
        elif name == "App":
            App = t
            print(f"✓ Found App")
    
    print()
    
    if not MainWindow:
        print("✗ MainWindow type not found")
        return False
    
    # Try to create MainWindow instance
    print("Creating MainWindow instance...")
    try:
        # Get the constructor
        constructor = MainWindow.GetConstructor(Reflection.BindingFlags.Public | Reflection.BindingFlags.Instance, None, [], None)
        
        if constructor:
            print("  ✓ Found constructor")
            
            # Create instance
            window = constructor.Invoke([])
            print(f"  ✓ Created instance: {window}")
            print(f"     Type: {type(window)}")
            
            # Check for events
            print()
            print("  Checking for events...")
            events = MainWindow.GetEvents()
            for event in events:
                print(f"    - {event.Name}")
            
            # Check for methods
            print()
            print("  Checking for methods...")
            methods = MainWindow.GetMethods(Reflection.BindingFlags.Public | Reflection.BindingFlags.Instance | Reflection.BindingFlags.DeclaredOnly)
            for method in methods[:10]:
                print(f"    - {method.Name}")
            
            return True
        else:
            print("  ✗ No public constructor found")
            
            # Try to find any constructor
            all_constructors = MainWindow.GetConstructors(Reflection.BindingFlags.Public | Reflection.BindingFlags.NonPublic | Reflection.BindingFlags.Instance)
            print(f"  Found {len(all_constructors)} constructors:")
            for ctor in all_constructors:
                params = ctor.GetParameters()
                param_str = ", ".join([f"{p.ParameterType.Name} {p.Name}" for p in params])
                print(f"    - {ctor.Name}({param_str})")
            
            return False
            
    except Exception as e:
        print(f"  ✗ Error creating instance: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print()
    print("=" * 70)
    print("Testing Direct Access to C# Types")
    print("=" * 70)
    print()
    
    try:
        import clr
    except ImportError:
        print("✗ pythonnet not installed")
        sys.exit(1)
    
    success = test_direct_access()
    
    print()
    print("=" * 70)
    if success:
        print("✓ Success! MainWindow can be created")
    else:
        print("✗ Failed to create MainWindow")
    print("=" * 70)
    print()
