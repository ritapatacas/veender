# VEENDER

> Have you been there?


VEENDER is a **face video finder**, a python tool to detect faces in local videos or YouTube links and extract matching frames and timestamps.

---

## Features

* Detect faces in long videos
* Download videos from YouTube
* Extract frames automatically
* Configurable frame skip and recognition tolerance

---

## Installation

```bash
git clone <your-repo-url> VEENDER
cd VEENDER
python setup.py
```

Activate the virtual environment:

```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```


---

## Configuration

Edit `config.yaml` to change defaults:

```yaml
frame_skip: 30
tolerance: 0.5
output_dir: "data/output"
faces_dir: "data/input/faces"
videos_dir: "data/input/videos"
```

---

## Usage

Local video:

```bash
python veender.py --video data/input/videos/yourvideo.mp4
```

YouTube video:

```bash
python veender.py --yt "https://www.youtube.com/watch?v=noJ9WNjkCT0"
```

Advanced options:

```bash
python veender.py --video yourvideo.mp4 --skip 10 --tolerance 0.4 --output "/path/to/results"
```

---

## Output

* Frames: `data/output/frames/<video_name>/frame_Xs.jpg`
* Log: `data/output/logs/<video_name>.log`

---

## Notes

* Ensure `yt-dlp` is installed
* Python 3.13+ required
* CLI flags override `config.yaml` defaults
