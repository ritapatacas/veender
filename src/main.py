import cv2
import face_recognition
import os
import sys
import glob
import numpy as np
import subprocess
import argparse
import yaml
import unicodedata
from tqdm import tqdm

# ========================
# Dependency check helper
# ========================
def safe_import(module_name, install_hint=None):
    try:
        return __import__(module_name)
    except ImportError as e:
        msg = f"[ERROR] Missing dependency: {module_name}.\n"
        if install_hint:
            msg += f"Install it with: {install_hint}\n"
        print(msg)
        sys.exit(1)


# ========================
# Utils
# ========================
def normalize_name(name: str) -> str:
    """Normalize a filename (remove spaces, accents, extension)."""
    name = os.path.splitext(os.path.basename(name))[0]
    name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode()
    name = name.replace(" ", "_")
    return name


def load_reference_faces(face_dir):
    """Load all reference faces and return the mean encoding."""
    encodings = []
    for file_path in glob.glob(os.path.join(face_dir, "*")):
        img = face_recognition.load_image_file(file_path)
        face_encs = face_recognition.face_encodings(img)
        if face_encs:
            encodings.append(face_encs[0])
            print(f"[INFO] Loaded reference face: {file_path}")
        else:
            print(f"[WARNING] No face found in {file_path}")

    if not encodings:
        raise ValueError("No reference faces found in face directory.")

    return np.mean(encodings, axis=0)


def download_video(url, output_dir):
    """Download a YouTube video using yt-dlp."""
    os.makedirs(output_dir, exist_ok=True)
    print(f"[INFO] Downloading video from {url}...")

    cmd = [
        "yt-dlp",
        "-f", "best[ext=mp4]",
        "-o", os.path.join(output_dir, "%(title)s.%(ext)s"),
        url,
    ]
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("[ERROR] yt-dlp not found. Install it with: pip install yt-dlp")
        sys.exit(1)

    files = sorted(glob.glob(os.path.join(output_dir, "*")), key=os.path.getmtime)
    if not files:
        raise FileNotFoundError("Download failed: no file found.")
    return files[-1]


def process_video(video_path, model_encoding, frame_skip, tolerance, output_dir):
    """Process the video and search for the reference face."""
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps

    print(f"[INFO] Processing video: {video_path}")
    print(f"[INFO] Duration: {duration/60:.2f} minutes, {frame_count} frames")

    frame_number = 0
    matches_times = []

    video_name = normalize_name(video_path)
    frames_dir = os.path.join(output_dir, "frames", video_name)
    os.makedirs(frames_dir, exist_ok=True)

    for _ in tqdm(range(frame_count), desc="Processing frames"):
        ret, frame = cap.read()
        if not ret:
            break

        if frame_number % frame_skip == 0:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for face_encoding in face_encodings:
                match = face_recognition.compare_faces([model_encoding], face_encoding, tolerance=tolerance)
                if match[0]:
                    timestamp = frame_number / fps
                    matches_times.append(timestamp)
                    print(f"[MATCH] Face found at {timestamp:.2f}s")

                    out_path = os.path.join(frames_dir, f"frame_{int(timestamp)}s.jpg")
                    cv2.imwrite(out_path, frame)
                    print(f"[INFO] Saved frame to {out_path}")

        frame_number += 1

    cap.release()
    return matches_times


# ========================
# Main
# ========================
def main():
    # Load defaults from config.yaml
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    parser = argparse.ArgumentParser(description="Find faces in videos")
    parser.add_argument("--video", type=str, help="Path to a video file")
    parser.add_argument("--yt", type=str, help="YouTube video URL")
    parser.add_argument("--skip", type=int, default=config.get("frame_skip", 30),
                        help="Process 1 frame every N frames")
    parser.add_argument("--tolerance", type=float, default=config.get("tolerance", 0.5),
                        help="Face recognition tolerance (lower = stricter)")
    parser.add_argument("--output", type=str, default=config.get("output_dir", "data/output"),
                        help="Directory for results")

    args = parser.parse_args()

    # Directories
    FACE_DIR = "data/input/face"
    VIDEO_DIR = "data/input/videos"
    OUTPUT_DIR = args.output

    # Load reference faces
    model_encoding = load_reference_faces(FACE_DIR)

    # Choose video
    if args.yt:
        video_path = download_video(args.yt, VIDEO_DIR)
    elif args.video:
        if not os.path.exists(args.video):
            raise FileNotFoundError(f"Video not found: {args.video}")
        video_path = args.video
    else:
        videos = glob.glob(os.path.join(VIDEO_DIR, "*"))
        if not videos:
            raise FileNotFoundError("No videos found in data/input/videos")
        video_path = videos[0]

    # Process video
    results = process_video(video_path, model_encoding,
                            frame_skip=args.skip,
                            tolerance=args.tolerance,
                            output_dir=OUTPUT_DIR)

    # Save results
    os.makedirs(os.path.join(OUTPUT_DIR, "logs"), exist_ok=True)
    log_file = os.path.join(OUTPUT_DIR, "logs", f"{normalize_name(video_path)}.log")
    with open(log_file, "w") as f:
        for t in results:
            f.write(f"{t:.2f}s\n")

    print(f"[INFO] Results saved to {log_file}")


if __name__ == "__main__":
    main()
