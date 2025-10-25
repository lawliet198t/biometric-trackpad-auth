#!/usr/bin/env python3
"""
Automatic Windows Touchpad Setup

Downloads and extracts the C# library automatically.
"""

import sys
import urllib.request
import zipfile
import json
import subprocess
import tempfile
from pathlib import Path
import shutil

# GitHub repository
GITHUB_REPO = "https://github.com/emoacht/RawInput.Touchpad.git"
GITHUB_API_URL = "https://api.github.com/repos/emoacht/RawInput.Touchpad/releases/latest"
DLL_NAME = "RawInput.Touchpad.dll"

def print_header(text):
    """Print a nice header"""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)

def check_existing_dll():
    """Check if DLL already exists"""
    possible_paths = [
        Path(DLL_NAME),
        Path("lib") / DLL_NAME,
        Path("bin") / DLL_NAME,
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return None

def get_latest_release_info():
    """Get latest release info from GitHub API"""
    print("Fetching latest release info from GitHub...")
    
    try:
        with urllib.request.urlopen(GITHUB_API_URL) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(f"✗ Error fetching release info: {e}")
        return None

def find_zip_asset(release_data):
    """Find the ZIP file in release assets"""
    if not release_data or 'assets' not in release_data:
        return None
    
    # Look for ZIP file
    for asset in release_data['assets']:
        if asset['name'].endswith('.zip'):
            return asset
    
    # If no ZIP, look for EXE
    for asset in release_data['assets']:
        if asset['name'].endswith('.exe'):
            return asset
    
    return None

def download_file(url, filename):
    """Download a file with progress"""
    print(f"Downloading {filename}...")
    
    try:
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, (downloaded / total_size) * 100)
                bar_length = 40
                filled = int(bar_length * percent / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                print(f'\r  [{bar}] {percent:.1f}%', end='', flush=True)
        
        urllib.request.urlretrieve(url, filename, reporthook=report_progress)
        print()  # New line after progress
        return True
    except Exception as e:
        print(f"\n✗ Error downloading: {e}")
        return False

def extract_dll_from_zip(zip_path, target_dir="."):
    """Extract DLL from ZIP file"""
    print(f"Extracting {DLL_NAME}...")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List all files in ZIP
            file_list = zip_ref.namelist()
            
            # Find the DLL
            dll_files = [f for f in file_list if f.endswith(DLL_NAME)]
            
            if not dll_files:
                print(f"⚠️  {DLL_NAME} not found in ZIP")
                print("  This release only contains an EXE file.")
                print("  You'll need to build from source to get the DLL.")
                print()
                print("  Options:")
                print("  1. Build from source (requires .NET SDK)")
                print("  2. Use the EXE with subprocess communication")
                print()
                print("  See README_WINDOWS_TOUCHPAD.md for instructions")
                return False
            
            # Extract the first matching DLL
            dll_file = dll_files[0]
            print(f"  Found: {dll_file}")
            
            # Extract to target directory
            zip_ref.extract(dll_file, target_dir)
            
            # Move to root if it's in a subdirectory
            extracted_path = Path(target_dir) / dll_file
            target_path = Path(target_dir) / DLL_NAME
            
            if extracted_path != target_path:
                # Create parent directories if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move the file
                shutil.move(str(extracted_path), str(target_path))
                
                # Clean up empty directories
                try:
                    extracted_path.parent.rmdir()
                except:
                    pass
            
            print(f"✓ Extracted to: {target_path.absolute()}")
            return True
            
    except Exception as e:
        print(f"✗ Error extracting: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_winget():
    """Check if winget is available"""
    try:
        result = subprocess.run(
            ["winget", "--version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

def install_with_winget(package_id, package_name):
    """Install a package using winget"""
    print(f"\nInstalling {package_name}...")
    print("This may take a few minutes...")
    
    try:
        result = subprocess.run(
            ["winget", "install", "--id", package_id, "--silent", "--accept-source-agreements", "--accept-package-agreements"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✓ {package_name} installed successfully")
            return True
        else:
            print(f"⚠️  Installation may have issues: {result.stderr}")
            # Sometimes winget returns non-zero even on success
            return True
    except Exception as e:
        print(f"✗ Error installing {package_name}: {e}")
        return False

def check_and_install_git():
    """Check if git is installed, install if not"""
    print("Checking for git...")
    
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ {version}")
            return True
    except FileNotFoundError:
        pass
    
    print("✗ git not found")
    
    # Try to install with winget
    if check_winget():
        print("Installing git automatically...")
        if install_with_winget("Git.Git", "git"):
            # Refresh PATH
            print("Verifying git installation...")
            try:
                result = subprocess.run(
                    ["git", "--version"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return True
            except:
                pass
            
            print("⚠️  git installed but not in PATH yet")
            print("   You may need to restart your terminal")
            print("   Or run: refreshenv (if using chocolatey)")
            return False
    else:
        print("✗ winget not available")
        print("  Install git manually: https://git-scm.com/download/win")
        print("  Or use: winget install Git.Git")
        return False

def check_and_install_dotnet():
    """Check if .NET SDK is installed, install if not"""
    print("Checking for .NET SDK...")
    
    try:
        result = subprocess.run(
            ["dotnet", "--version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ .NET SDK {version} is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("✗ .NET SDK not found")
    
    # Try to install with winget
    if check_winget():
        print("Installing .NET SDK automatically...")
        if install_with_winget("Microsoft.DotNet.SDK.8", ".NET SDK"):
            # Refresh PATH
            print("Verifying .NET SDK installation...")
            try:
                result = subprocess.run(
                    ["dotnet", "--version"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return True
            except:
                pass
            
            print("⚠️  .NET SDK installed but not in PATH yet")
            print("   You may need to restart your terminal")
            return False
    else:
        print("✗ winget not available")
        print("  Install .NET SDK manually: https://dotnet.microsoft.com/download")
        print("  Or use: winget install Microsoft.DotNet.SDK.8")
        return False

def build_from_source():
    """Clone repository and build DLL from source"""
    print("\nBuilding DLL from source...")
    print("This will take a few minutes...")
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        repo_path = temp_path / "RawInput.Touchpad"
        
        try:
            # Clone repository
            print("\n1. Cloning repository...")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", GITHUB_REPO, str(repo_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"✗ Failed to clone: {result.stderr}")
                return False
            
            print("✓ Repository cloned")
            
            # Build project
            print("\n2. Building project...")
            source_path = repo_path / "Source"
            
            result = subprocess.run(
                ["dotnet", "build", "-c", "Release"],
                cwd=str(source_path),
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"✗ Build failed: {result.stderr}")
                return False
            
            print("✓ Build successful")
            
            # Find and copy DLL
            print("\n3. Finding built DLL...")
            
            # Search recursively for the DLL
            dll_found = None
            for dll_path in repo_path.rglob(DLL_NAME):
                # Skip obj directories
                if "obj" not in str(dll_path):
                    dll_found = dll_path
                    print(f"  Found: {dll_path}")
                    break
            
            if not dll_found:
                print("✗ Could not find built DLL")
                print("  Searching entire build output...")
                
                # List all DLLs found
                all_dlls = list(repo_path.rglob("*.dll"))
                if all_dlls:
                    print("  Found these DLLs:")
                    for dll in all_dlls[:10]:  # Show first 10
                        print(f"    - {dll}")
                else:
                    print("  No DLLs found in build output")
                
                return False
            
            print("\n4. Copying DLL...")
            
            # Copy to project directory
            target_path = Path(DLL_NAME)
            shutil.copy(str(dll_found), str(target_path))
            
            print(f"✓ DLL copied to: {target_path.absolute()}")
            return True
            
        except Exception as e:
            print(f"✗ Error during build: {e}")
            import traceback
            traceback.print_exc()
            return False

def install_pythonnet():
    """Install pythonnet if not already installed"""
    print("Checking for pythonnet...")
    
    try:
        import clr
        print("✓ pythonnet is already installed")
        return True
    except ImportError:
        print("⚠️  pythonnet not installed")
        print("Installing pythonnet...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "pythonnet"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✓ pythonnet installed successfully")
                return True
            else:
                print(f"✗ Failed to install pythonnet: {result.stderr}")
                return False
        except Exception as e:
            print(f"✗ Error installing pythonnet: {e}")
            return False

def main():
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Windows Touchpad Automatic Setup" + " " * 21 + "║")
    print("╚" + "=" * 68 + "╝")
    
    # Step 1: Check if DLL already exists
    print_header("Step 1: Checking for existing DLL")
    existing_dll = check_existing_dll()
    
    if existing_dll:
        print(f"✓ Found existing DLL: {existing_dll.absolute()}")
        response = input("\nDo you want to download the latest version anyway? (y/N): ")
        if response.lower() != 'y':
            print("Using existing DLL")
            skip_download = True
        else:
            skip_download = False
    else:
        print(f"✗ {DLL_NAME} not found")
        skip_download = False
    
    # Step 2: Build DLL from source
    if not skip_download:
        print_header("Step 2: Building C# Library from Source")
        
        # Check and install prerequisites
        print("Checking and installing prerequisites...")
        
        has_git = check_and_install_git()
        has_dotnet = check_and_install_dotnet()
        
        if not has_git or not has_dotnet:
            print("\n" + "=" * 70)
            print("⚠️  PREREQUISITES MISSING")
            print("=" * 70)
            print()
            
            if not has_git:
                print("git is required but could not be installed automatically.")
                print("  Install manually: https://git-scm.com/download/win")
                print("  Or use: winget install Git.Git")
                print()
            
            if not has_dotnet:
                print(".NET SDK is required but could not be installed automatically.")
                print("  Install manually: https://dotnet.microsoft.com/download")
                print("  Or use: winget install Microsoft.DotNet.SDK.8")
                print()
            
            print("After installing, restart your terminal and run this script again.")
            print()
            return 1
        
        print("\n✓ All prerequisites ready")
        
        # Build from source
        if not build_from_source():
            print("\n" + "=" * 70)
            print("⚠️  BUILD FAILED")
            print("=" * 70)
            print()
            print("Options:")
            print("1. Check error messages above")
            print("2. Try manual build (see README_WINDOWS_TOUCHPAD.md)")
            print("3. Use Linux (works out of the box!)")
            print()
            return 1
    
    # Step 3: Install pythonnet
    print_header("Step 3: Installing Python.NET")
    
    if not install_pythonnet():
        print("\n⚠️  pythonnet installation failed")
        print("Try manually: pip install pythonnet")
        return 1
    
    # Step 4: Verify setup
    print_header("Step 4: Verifying Setup")
    
    # Check if DLL exists
    dll_path = check_existing_dll()
    if not dll_path:
        print("✗ DLL not found after build")
        print("  Something went wrong during the build process")
        return 1
    
    print(f"✓ DLL exists: {dll_path.absolute()}")
    
    # Check pythonnet
    try:
        import clr
        print("✓ pythonnet is installed")
    except ImportError:
        print("✗ pythonnet not installed")
        return 1
    
    # Try to load DLL
    print("\nTesting DLL load...")
    try:
        clr.AddReference(str(dll_path.absolute()))
        print("✓ DLL loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load DLL: {e}")
        return 1
    
    # Try to import classes
    print("\nTesting class imports...")
    try:
        # List available types
        import System
        assembly = System.Reflection.Assembly.LoadFrom(str(dll_path.absolute()))
        types = list(assembly.GetTypes())
        
        print(f"✓ Found {len(types)} types in DLL:")
        for t in types[:5]:  # Show first 5
            print(f"    - {t.FullName}")
        if len(types) > 5:
            print(f"    ... and {len(types) - 5} more")
        
    except Exception as e:
        print(f"⚠️  Could not list types: {e}")
    
    print_header("🎉 SUCCESS!")
    print("Your Windows multi-touch setup is complete!")
    print()
    print("Next steps:")
    print("  1. Run: python realtime_trainer.py")
    print("  2. Touch your touchpad with multiple fingers")
    print("  3. Enjoy true multi-touch! 🎉")
    print()
    print("Note: The exact class names may need adjustment in")
    print("      windows_touchpad_pythonnet.py based on the types shown above.")
    print()
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
