#!/usr/bin/env python3
"""
Debug DLL Loading Issues

Shows detailed information about why a DLL can't be loaded.
"""

import sys
from pathlib import Path

try:
    import clr
except ImportError:
    print("✗ pythonnet not installed")
    print("  Install with: pip install pythonnet")
    sys.exit(1)

def debug_dll_load(dll_path):
    """Debug DLL loading with detailed error information"""
    
    dll_path = Path(dll_path)
    
    if not dll_path.exists():
        print(f"✗ DLL not found: {dll_path}")
        return False
    
    print(f"Debugging DLL: {dll_path.absolute()}")
    print()
    
    # Step 1: Load required .NET assemblies
    print("Step 1: Loading .NET Framework assemblies...")
    try:
        import System
        clr.AddReference("System")
        print("  ✓ System")
        
        clr.AddReference("System.Windows.Forms")
        print("  ✓ System.Windows.Forms")
        
        clr.AddReference("System.Drawing")
        print("  ✓ System.Drawing")
        
        clr.AddReference("System.Core")
        print("  ✓ System.Core")
        
    except Exception as e:
        print(f"  ✗ Error loading .NET assemblies: {e}")
        return False
    
    print()
    
    # Step 2: Add DLL directory to path
    print("Step 2: Adding DLL directory to path...")
    dll_dir = str(dll_path.parent.absolute())
    if dll_dir not in sys.path:
        sys.path.append(dll_dir)
        print(f"  ✓ Added: {dll_dir}")
    else:
        print(f"  ✓ Already in path: {dll_dir}")
    
    print()
    
    # Step 3: Try to load the DLL
    print("Step 3: Loading DLL...")
    try:
        # Try by name first
        try:
            clr.AddReference(dll_path.stem)
            print(f"  ✓ Loaded by name: {dll_path.stem}")
        except:
            # Try by full path
            clr.AddReference(str(dll_path.absolute()))
            print(f"  ✓ Loaded by path: {dll_path.absolute()}")
    except Exception as e:
        print(f"  ✗ Failed to load DLL: {e}")
        return False
    
    print()
    
    # Step 4: Load assembly and inspect
    print("Step 4: Inspecting assembly...")
    try:
        import System.Reflection as Reflection
        
        assembly = Reflection.Assembly.LoadFrom(str(dll_path.absolute()))
        print(f"  ✓ Assembly loaded: {assembly.FullName}")
        print()
        
        # Try to get types
        print("Step 5: Getting types...")
        try:
            types = assembly.GetTypes()
            print(f"  ✓ Found {len(types)} types")
            print()
            
            print("Available types:")
            for i, t in enumerate(types):
                print(f"  {i+1}. {t.FullName}")
                
                # Show public methods for first few types
                if i < 3:
                    methods = t.GetMethods(
                        Reflection.BindingFlags.Public | 
                        Reflection.BindingFlags.Instance |
                        Reflection.BindingFlags.DeclaredOnly
                    )
                    if methods:
                        print(f"     Methods:")
                        for method in methods[:5]:
                            print(f"       - {method.Name}")
                        if len(methods) > 5:
                            print(f"       ... and {len(methods) - 5} more")
                print()
            
            return True
            
        except Reflection.ReflectionTypeLoadException as rtle:
            print(f"  ⚠️  ReflectionTypeLoadException")
            print()
            print("LoaderExceptions (detailed):")
            
            for i, ex in enumerate(rtle.LoaderExceptions):
                if ex:
                    print(f"\n  Exception {i+1}:")
                    print(f"    Type: {ex.GetType().Name}")
                    print(f"    Message: {ex.Message}")
                    
                    # Try to get more details
                    if hasattr(ex, 'FusionLog'):
                        print(f"    Fusion Log: {ex.FusionLog}")
            
            print()
            print("This usually means:")
            print("  1. Missing dependencies (other DLLs)")
            print("  2. Wrong .NET Framework version")
            print("  3. Missing native libraries")
            print()
            
            # Show which types DID load
            if rtle.Types:
                loaded_types = [t for t in rtle.Types if t is not None]
                if loaded_types:
                    print(f"Successfully loaded {len(loaded_types)} types:")
                    for t in loaded_types[:5]:
                        print(f"  - {t.FullName}")
                    if len(loaded_types) > 5:
                        print(f"  ... and {len(loaded_types) - 5} more")
            
            return False
            
        except Exception as e:
            print(f"  ✗ Error getting types: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"  ✗ Error loading assembly: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_dll_load.py <path-to-dll>")
        print()
        print("Example:")
        print("  python debug_dll_load.py RawInput.Touchpad.dll")
        sys.exit(1)
    
    dll_path = sys.argv[1]
    
    print("=" * 70)
    print("DLL Loading Debugger")
    print("=" * 70)
    print()
    
    success = debug_dll_load(dll_path)
    
    print()
    print("=" * 70)
    if success:
        print("✓ DLL loaded successfully!")
    else:
        print("✗ DLL loading failed")
        print()
        print("Next steps:")
        print("  1. Check the error messages above")
        print("  2. Make sure all dependencies are available")
        print("  3. Try building with a different .NET version")
        print("  4. Consider using subprocess communication instead")
    print("=" * 70)
