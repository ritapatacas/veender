import streamlit as st
import subprocess
import tempfile
import cv2
import numpy as np
from pathlib import Path

st.set_page_config(page_title="YouTube Frame Extractor", page_icon="🎥", layout="wide")
st.title("YouTube Frame Extractor (1 FPS Test)")

# Input for YouTube URL
youtube_url = st.text_input("YouTube link", placeholder="https://youtube.com/watch?v=...")

if st.button("🎬 Test Video Processing"):
    if not youtube_url:
        st.error("⚠️ Please provide a YouTube link.")
    else:
        st.info("Fetching direct stream URL...")
        try:
            # Get direct video URL using yt-dlp -g
            cmd = ["yt-dlp", "-g", "-f", "worst[ext=mp4]", youtube_url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                st.error(f"❌ Failed to get video URL: {result.stderr}")
                st.stop()

            direct_url = result.stdout.strip()
            st.write("Direct video URL:", direct_url)

            # Open video stream directly with OpenCV
            cap = cv2.VideoCapture(direct_url)
            if not cap.isOpened():
                st.error("❌ Could not open video stream.")
                st.stop()

            fps = int(cap.get(cv2.CAP_PROP_FPS))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            st.write(f"Video FPS: {fps}, Total Frames (approx): {total_frames}")

            frames_captured = []
            frame_count = 0
            max_frames = 10

            st.info("Capturing up to 10 frames (1 per second)...")
            
            while len(frames_captured) < max_frames:
                cap.set(cv2.CAP_PROP_POS_MSEC, frame_count * 1000)  # Jump to next second
                ret, frame = cap.read()
                if not ret:
                    break

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames_captured.append(frame_rgb)
                frame_count += 1

            cap.release()

            if frames_captured:
                st.success(f"Captured {len(frames_captured)} frames!")
                cols = st.columns(min(5, len(frames_captured)))
                for i, frame in enumerate(frames_captured):
                    with cols[i % 5]:
                        st.image(frame, caption=f"Frame {i+1}", use_container_width=True)
            else:
                st.warning("No frames captured. Possibly a protected or inaccessible stream.")

        except subprocess.TimeoutExpired:
            st.error("❌ yt-dlp request timed out.")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

st.markdown("---")
st.markdown("**Powered by yt-dlp + OpenCV**")
