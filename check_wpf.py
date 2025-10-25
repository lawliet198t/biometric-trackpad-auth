#!/usr/bin/env python3
"""
Check WPF Installation

Verifies that WPF assemblies can be loaded.
"""

import sys

try:
    import clr
except ImportError:
    print("✗ pythonnet not installed")
    sys.exit(1)

print("Checking .NET assemblies...")
print()

# Try to load basic assemblies
assemblies_to_check = [
    ("System", "Basic .NET"),
    ("System.Windows.Forms", "Windows Forms"),
    ("System.Drawing", "Drawing"),
    ("System.Core", "Core"),
    ("PresentationFramework", "WPF Framework"),
    ("PresentationCore", "WPF Core"),
    ("WindowsBase", "WPF Base"),
]

loaded = []
failed = []

for assembly_name, description in assemblies_to_check:
    try:
        clr.AddReference(assembly_name)
        print(f"✓ {assembly_name:25} ({description})")
        loaded.append(assembly_name)
    except Exception as e:
        print(f"✗ {assembly_name:25} ({description})")
        print(f"  Error: {str(e)[:80]}")
        failed.append((assembly_name, e))

print()
print("=" * 70)
print(f"Summary: {len(loaded)}/{len(assemblies_to_check)} assemblies loaded")
print("=" * 70)

if failed:
    print()
    print("Failed assemblies:")
    for name, error in failed:
        print(f"  - {name}")
    
    # Check if WPF is the issue
    wpf_assemblies = ["PresentationFramework", "PresentationCore", "WindowsBase"]
    if any(name in wpf_assemblies for name, _ in failed):
        print()
        print("WPF assemblies are missing!")
        print()
        print("Solutions:")
        print()
        print("1. Restart your terminal/PowerShell and try again")
        print("   (The PATH may need to be refreshed)")
        print()
        print("2. Check if .NET Desktop Runtime is really installed:")
        print("   Run: dotnet --list-runtimes")
        print()
        print("3. Try installing .NET Desktop Runtime 6.0 or 8.0 instead:")
        print("   winget install Microsoft.DotNet.DesktopRuntime.6")
        print("   or")
        print("   winget install Microsoft.DotNet.DesktopRuntime.8")
        print()
        print("4. Use the subprocess approach (no WPF needed)")
else:
    print()
    print("✓ All assemblies loaded successfully!")
    print()
    print("You should be able to use the Windows touchpad now.")
    print("Run: python test_windows_multitouch.py")
