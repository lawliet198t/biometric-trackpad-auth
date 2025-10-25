#!/usr/bin/env python3
"""
Automatic Windows Touchpad Setup

Downloads and extracts the C# library automatically.
"""

import sys
import urllib.request
import zipfile
import json
from pathlib import Path
import shutil

# GitHub API URL for latest release
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
    
    for asset in release_data['assets']:
        if asset['name'].endswith('.zip'):
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
                print(f"✗ {DLL_NAME} not found in ZIP")
                print("  Available files:")
                for f in file_list:
                    print(f"    - {f}")
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
            import subprocess
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
    
    # Step 2: Download and extract DLL
    if not skip_download:
        print_header("Step 2: Downloading C# Library")
        
        # Get latest release info
        release_data = get_latest_release_info()
        
        if not release_data:
            print("\n✗ Could not fetch release info")
            print("Manual download:")
            print("  1. Go to: https://github.com/emoacht/RawInput.Touchpad/releases")
            print("  2. Download the latest ZIP file")
            print(f"  3. Extract {DLL_NAME} to this folder")
            return 1
        
        print(f"✓ Latest version: {release_data.get('tag_name', 'unknown')}")
        
        # Find ZIP asset
        zip_asset = find_zip_asset(release_data)
        
        if not zip_asset:
            print("\n✗ Could not find ZIP file in release")
            print("Manual download:")
            print(f"  Go to: {release_data.get('html_url', 'GitHub releases')}")
            return 1
        
        print(f"✓ Found: {zip_asset['name']}")
        
        # Download ZIP
        zip_filename = zip_asset['name']
        if not download_file(zip_asset['browser_download_url'], zip_filename):
            return 1
        
        print(f"✓ Downloaded: {zip_filename}")
        
        # Extract DLL
        if not extract_dll_from_zip(zip_filename):
            return 1
        
        # Clean up ZIP file
        try:
            Path(zip_filename).unlink()
            print(f"✓ Cleaned up: {zip_filename}")
        except:
            pass
    
    # Step 3: Install pythonnet
    print_header("Step 3: Installing Python.NET")
    
    if not install_pythonnet():
        print("\n⚠️  pythonnet installation failed")
        print("Try manually: pip install pythonnet")
        return 1
    
    # Step 4: Verify setup
    print_header("Step 4: Verifying Setup")
    
    print("Running verification tests...")
    print()
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "test_windows_multitouch.py"],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print_header("🎉 SUCCESS!")
            print("Your Windows multi-touch setup is complete!")
            print()
            print("Next steps:")
            print("  1. Run: python realtime_trainer.py")
            print("  2. Touch your touchpad with multiple fingers")
            print("  3. Enjoy true multi-touch! 🎉")
            print()
            return 0
        else:
            print_header("⚠️  SETUP INCOMPLETE")
            print("Some tests failed. See above for details.")
            print()
            print("For help, see: SETUP_WINDOWS_MULTITOUCH.md")
            print()
            return 1
            
    except FileNotFoundError:
        print("✓ Setup files are ready")
        print()
        print("To verify, run: python test_windows_multitouch.py")
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
