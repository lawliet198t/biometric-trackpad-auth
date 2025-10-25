#!/usr/bin/env python3
"""
Automatically patch RawInput.Touchpad to add JSON output
"""

import re
from pathlib import Path

def patch_mainwindow():
    """Add JSON output to MainWindow.xaml.cs"""
    
    source_file = Path("RawInput.Touchpad/Source/RawInput.Touchpad/MainWindow.xaml.cs")
    
    if not source_file.exists():
        print(f"✗ Source file not found: {source_file}")
        print("  Run build_touchpad.bat first")
        return False
    
    print(f"Reading: {source_file}")
    content = source_file.read_text(encoding='utf-8')
    
    # Backup
    backup_file = source_file.with_suffix('.cs.backup')
    if not backup_file.exists():
        backup_file.write_text(content, encoding='utf-8')
        print(f"✓ Backup created: {backup_file}")
    
    # Check if already patched
    if 'JSON output for Python' in content:
        print("✓ Already patched!")
        return True
    
    # Add using statement for JSON
    if 'using System.Text.Json;' not in content:
        content = content.replace(
            'using System.Windows;',
            'using System.Windows;\nusing System.Text.Json;'
        )
        print("✓ Added JSON using statement")
    
    # Find where contacts are processed
    # Look for patterns like: foreach (var contact in contacts)
    # or where contact data is displayed
    
    # Pattern 1: Find where contacts are used to update UI
    pattern1 = r'(foreach\s*\(\s*var\s+\w+\s+in\s+\w*[Cc]ontacts?\w*\s*\))'
    matches = list(re.finditer(pattern1, content))
    
    if matches:
        print(f"✓ Found {len(matches)} contact processing locations")
        
        # Add JSON output after the first foreach
        match = matches[0]
        insert_pos = match.end()
        
        # Find the opening brace
        brace_pos = content.find('{', insert_pos)
        if brace_pos != -1:
            # Insert JSON output code
            json_code = '''
                
                // JSON output for Python
                try
                {
                    var contactList = contacts.Select(c => new
                    {
                        ContactId = c.ContactId,
                        X = c.X,
                        Y = c.Y,
                        Timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
                    }).ToList();
                    
                    if (contactList.Any())
                    {
                        var json = JsonSerializer.Serialize(new
                        {
                            Type = "contacts",
                            Contacts = contactList
                        });
                        Console.WriteLine(json);
                        Console.Out.Flush();
                    }
                }
                catch { }
'''
            
            content = content[:brace_pos+1] + json_code + content[brace_pos+1:]
            print("✓ Added JSON output code")
    else:
        print("⚠️  Could not find contact processing code")
        print("   Manual patching required")
        return False
    
    # Add using System.Linq if not present
    if 'using System.Linq;' not in content:
        content = content.replace(
            'using System.Windows;',
            'using System.Windows;\nusing System.Linq;'
        )
    
    # Write patched file
    source_file.write_text(content, encoding='utf-8')
    print(f"✓ Patched: {source_file}")
    
    return True


def rebuild():
    """Rebuild the patched project"""
    import subprocess
    
    print("\nRebuilding...")
    result = subprocess.run(
        ["dotnet", "build", "-c", "Release"],
        cwd="RawInput.Touchpad/Source",
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ Build successful")
        return True
    else:
        print("✗ Build failed:")
        print(result.stderr)
        return False


def copy_files():
    """Copy built files"""
    import shutil
    
    source_exe = Path("RawInput.Touchpad/Source/RawInput.Touchpad/bin/Release/net5.0-windows/RawInput.Touchpad.exe")
    source_dll = Path("RawInput.Touchpad/Source/RawInput.Touchpad/bin/Release/net5.0-windows/RawInput.Touchpad.dll")
    
    if source_exe.exists():
        shutil.copy(source_exe, ".")
        print(f"✓ Copied: {source_exe.name}")
    
    if source_dll.exists():
        shutil.copy(source_dll, ".")
        print(f"✓ Copied: {source_dll.name}")


if __name__ == "__main__":
    print("=" * 70)
    print("Patching RawInput.Touchpad for JSON Output")
    print("=" * 70)
    print()
    
    if patch_mainwindow():
        print()
        if rebuild():
            print()
            copy_files()
            print()
            print("=" * 70)
            print("✓ Success!")
            print("=" * 70)
            print()
            print("Test it:")
            print("  .\\RawInput.Touchpad.exe")
            print()
            print("You should see JSON output when touching the touchpad!")
        else:
            print()
            print("Build failed. Check errors above.")
    else:
        print()
        print("Patching failed. Manual editing required.")
        print("See: patch_rawinput.bat for instructions")
