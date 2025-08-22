# VEENDER

> Have you been there?

VEENDER is a **face video finder**, a python tool to detect faces in local videos or YouTube links and extract matching frames and timestamps.

---

## 🚀 Quick Installation (One-time setup)

### Option 1: Direct pip install (Recommended)
```bash
pip install veender
```

### Option 2: One-liner installers
```bash
# Cross-platform Python installer
curl -sSL https://raw.githubusercontent.com/ritapatacas/veender/main/install.py | python3

# Unix/macOS/Linux
curl -sSL https://raw.githubusercontent.com/ritapatacas/veender/main/install.sh | bash

# Windows
curl -sSL https://raw.githubusercontent.com/ritapatacas/veender/main/install.bat | cmd
```

### Option 3: Development installation
```bash
git clone https://github.com/ritapatacas/veender.git
cd veender
pip install -e .
```

---

## 🎬 Usage

After installation, you can use `veender` command directly:

### Local video:
```bash
veender --video data/input/videos/yourvideo.mp4
```

### YouTube video:
```bash
veender --yt "https://www.youtube.com/watch?v=noJ9WNjkCT0"
```

### Advanced options:
```bash
veender --video yourvideo.mp4 --skip 10 --tolerance 0.4 --output "/path/to/results"
```

### If using virtual environment:
```bash
# Option 1: Activate environment first
source veender_env/bin/activate  # Unix/Mac
# veender_env\Scripts\activate.bat  # Windows
veender --video example.mp4

# Option 2: Use the runner script (no activation needed)
python run.py --video example.mp4
```

---

## ⚙️ Configuration

Edit `config.yaml` to change defaults:

```yaml
frame_skip: 30
tolerance: 0.5
output_dir: "data/output"
faces_dir: "data/input/face"
videos_dir: "data/input/videos"
```

---

## 📁 Setup

1. Add face photos to: `data/input/face/`
2. Add videos to: `data/input/videos/`
3. Run veender with your preferred method above

---

## 📤 Output

* Frames: `data/output/frames/<video_name>/frame_Xs.jpg`
* Log: `data/output/logs/<video_name>.log`

---

## 🔧 Requirements

* Python 3.8+
* yt-dlp for YouTube downloads
* OpenCV, dlib, face_recognition libraries

---
