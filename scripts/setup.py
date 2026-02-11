import subprocess
import sys
import shutil

REQUIRED_BREW_PACKAGES = [
    "blueutil",   # Bluetooth control
    "ffmpeg",     # Vision/Video processing
    "poppler",    # PDF processing
    "git"         # Version control
]

def check_command(cmd):
    """Check if a command exists in the path."""
    return shutil.which(cmd) is not None

def run_command(cmd):
    """Run a shell command and print output."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True

def is_brew_package_installed(package):
    """Check if a brew package is installed."""
    result = subprocess.run(f"brew list {package}", shell=True, text=True, capture_output=True)
    return result.returncode == 0

def install_dependencies():
    print("🚀 ARKA V2: Checking System Dependencies...")
    
    # Check for Homebrew
    if not check_command("brew"):
        print("❌ Homebrew not found. Please install Homebrew first.")
        sys.exit(1)

    # Check and Install Packages
    for package in REQUIRED_BREW_PACKAGES:
        if is_brew_package_installed(package):
            print(f"✅ {package} is already installed.")
        else:
            print(f"⚠️  {package} missing. Installing...")
            if run_command(f"brew install {package}"):
                print(f"✅ {package} installed.")
            else:
                print(f"❌ Failed to install {package}.")
                sys.exit(1)
    
    print("\n✅ All System Dependencies Verified!")

if __name__ == "__main__":
    install_dependencies()
