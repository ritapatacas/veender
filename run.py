#!/usr/bin/env python3
"""
VEENDER Runner
Quick launcher for the VEENDER face finder tool
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def main():
    print("🎬 VEENDER - Face Finder Runner")
    print("===============================\n")
    
    # Determine OS and venv paths
    is_windows = platform.system() == "Windows"
    
    if is_windows:
        venv_python = Path("veender_env/Scripts/python.exe")
        activate_cmd = "veender_env\\Scripts\\activate.bat"
    else:
        venv_python = Path("veender_env/bin/python")
        activate_cmd = "source veender_env/bin/activate"
    
    # Check if virtual environment exists
    if not venv_python.exists():
        print("❌ VEENDER environment not found!")
        print("   Please run the installer first:")
        print("   • Python: python install.py")
        print("   • Unix/Mac: bash install.sh")
        print("   • Windows: install.bat")
        sys.exit(1)
    
    print("✅ VEENDER environment found")
    
    # Get command line arguments (pass through to veender)
    veender_args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    if not veender_args:
        print("🤔 No arguments provided. Here are some examples:")
        print("   • Local video: python run.py --video data/input/videos/example.mp4")
        print("   • YouTube: python run.py --yt 'https://youtube.com/watch?v=VIDEO_ID'")
        print("   • Custom settings: python run.py --video video.mp4 --skip 10 --tolerance 0.4")
        print(f"\n💡 Or activate the environment manually: {activate_cmd}")
        print("   Then run: veender [options]")
        return
    
    # Run veender with provided arguments
    print(f"🚀 Running: veender {' '.join(veender_args)}")
    try:
        subprocess.run([str(venv_python), "-m", "veender"] + veender_args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running VEENDER: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")

if __name__ == "__main__":
    main()
