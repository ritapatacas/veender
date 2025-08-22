import os
import subprocess
import venv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
VENV_DIR = ROOT_DIR / "venv"
REQ_FILE = ROOT_DIR / "requirements.txt"

def create_virtualenv():
    """Create a virtual environment if it doesn't exist"""
    if not VENV_DIR.exists():
        print("[INFO] Creating virtual environment...")
        venv.EnvBuilder(with_pip=True).create(str(VENV_DIR))
    else:
        print("[INFO] Virtual environment already exists.")

def install_requirements():
    """Install requirements inside the venv"""
    print("[INFO] Installing dependencies...")
    pip_executable = VENV_DIR / ("Scripts/pip.exe" if os.name == "nt" else "bin/pip")
    subprocess.check_call([str(pip_executable), "install", "--upgrade", "pip"])
    subprocess.check_call([str(pip_executable), "install", "-r", str(REQ_FILE)])

if __name__ == "__main__":
    create_virtualenv()
    install_requirements()

    print("\n✅ Setup complete!")
    if os.name == "nt":
        print("➡️ To activate venv: venv\\Scripts\\activate")
    else:
        print("➡️ To activate venv: source venv/bin/activate")
    print("➡️ To run the script: python veender.py --video data/input/videos/example.mp4")
