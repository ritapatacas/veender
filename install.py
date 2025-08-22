#!/usr/bin/env python3
"""
VEENDER Quick Installer
One-command setup for the VEENDER face finder tool
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, shell=False):
    """Run command and handle errors"""
    try:
        result = subprocess.run(cmd, shell=shell, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        print(f"   {e.stderr}")
        sys.exit(1)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ is required. Found: {version.major}.{version.minor}")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")

def main():
    print("🚀 VEENDER - Quick Installer")
    print("=============================\n")
    
    check_python_version()
    
    # Determine OS
    is_windows = platform.system() == "Windows"
    venv_activate = "veender_env\\Scripts\\activate.bat" if is_windows else "source veender_env/bin/activate"
    
    # Create virtual environment
    print("📦 Setting up virtual environment...")
    run_command([sys.executable, "-m", "venv", "veender_env"])
    
    # Determine pip path
    if is_windows:
        pip_path = Path("veender_env/Scripts/pip.exe")
        python_path = Path("veender_env/Scripts/python.exe")
    else:
        pip_path = Path("veender_env/bin/pip")
        python_path = Path("veender_env/bin/python")
    
    # Upgrade pip
    print("⬆️ Upgrading pip...")
    run_command([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install VEENDER
    print("⬇️ Installing VEENDER...")
    run_command([str(pip_path), "install", "veender"])  # Once published to PyPI
    
    # Create directory structure
    print("📁 Creating directory structure...")
    dirs = [
        "data/input/face",
        "data/input/videos", 
        "data/output/frames",
        "data/output/logs"
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create config if it doesn't exist
    if not Path("config.yaml").exists():
        print("⚙️ Creating default config...")
        config_content = """# VEENDER Configuration
frame_skip: 30
tolerance: 0.5
output_dir: "data/output"
faces_dir: "data/input/face"
videos_dir: "data/input/videos"
"""
        with open("config.yaml", "w") as f:
            f.write(config_content)
    
    print("\n🎉 Installation complete!\n")
    print("📋 Quick start:")
    print("   1. Add face photos to: data/input/face/")
    print("   2. Add videos to: data/input/videos/")
    print("   3. Run: veender --video path/to/video.mp4")
    print("   4. Or try YouTube: veender --yt 'https://youtube.com/watch?v=VIDEO_ID'")
    print(f"\n💡 To activate environment: {venv_activate}")
    print("💡 To deactivate: deactivate")
    print("\n🎯 VEENDER is now installed and ready to use!")

if __name__ == "__main__":
    main()

