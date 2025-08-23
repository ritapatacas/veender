import streamlit as st
from pathlib import Path
import subprocess
import tempfile
import shutil
import re
from PIL import Image
import queue
import threading
import time
import os
import signal

st.set_page_config(page_title="VEENDER", page_icon="🎥", layout="wide")

st.markdown("<h1 style='text-align: center;'>VEENDER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; margin: 0;'>been there?</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; font-style: bold; margin: 0;'>self stalker - find yourself in a video</b></p>", unsafe_allow_html=True)
# Initialize session state for UI visibility
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Create containers for different states
input_container = st.container()
processing_container = st.container()

# Only show interface if not processing
if not st.session_state.processing:
    with input_container:
        st.write("Upload face images and a YouTube link.")
        
        # -----------------------------
        # Upload inputs - Compact Layout
        # -----------------------------
        
        # 1. Smaller face upload section
        face_files = st.file_uploader(
            "📸 Face images", 
            type=["jpg", "jpeg", "png"], 
            accept_multiple_files=True,
            help="Upload up to 5 reference face images"
        )
        
        if face_files and len(face_files) > 5:
            st.warning("⚠️ Maximum of 5 face images allowed.")
            face_files = face_files[:5]
        
        # 2. YouTube URL input only (removed local video upload)
        youtube_url = st.text_input("🎬 YouTube link", placeholder="https://youtube.com/watch?v=...")
        
        # 3. Side-by-side sliders in columns (smaller)
        col1, col2 = st.columns(2)
        with col1:
            skip = st.slider("⏭️ Frame skip", min_value=1, max_value=200, value=30, help="Recommended: 10-50")
        with col2:
            tolerance = st.slider("🎯 Match tolerance", min_value=0.1, max_value=1.0, value=0.5, help="Recommended: 0.3-0.6")
        
        # -----------------------------
        # Run VEENDER
        # -----------------------------
        if st.button("🚀 RUN VEENDER", type="primary", use_container_width=True):
            if not face_files:
                st.error("⚠️ Please upload at least one face image.")
            elif not youtube_url:
                st.error("⚠️ Please paste a YouTube link.")
            else:
                # Store values in session state and start processing
                st.session_state.processing = True
                st.session_state.face_files = face_files
                st.session_state.youtube_url = youtube_url
                st.session_state.skip = skip
                st.session_state.tolerance = tolerance
                st.rerun()

# Show processing interface when running (hides all input elements)
elif st.session_state.processing:
    with processing_container:
        
        # Processing with logs and frame display
        with tempfile.TemporaryDirectory() as tmpdir:
            # Prepare face folder
            face_dir = Path("data/input/face")
            face_dir.mkdir(parents=True, exist_ok=True)

            # Clear old faces
            for old in face_dir.glob("*"):
                old.unlink()

            # Save uploaded faces
            for f in st.session_state.face_files:
                with open(face_dir / f.name, "wb") as out:
                    out.write(f.read())

            # Prepare video argument for YouTube
            video_args = ["--yt", st.session_state.youtube_url]

            # Build command
            cmd = [
                "python", "src/main.py",
                "--skip", str(st.session_state.skip),
                "--tolerance", str(st.session_state.tolerance),
                "--output", str(tmpdir)
            ] + video_args

            st.info("🔄 Running VEENDER... this may take a while")
            
            # Container for frames above logs
            frames_container = st.container()
            
            logs_container = st.empty()
            logs = []
            frames_displayed = set()
            frames_dir = Path(tmpdir) / "frames"

            # -----------------------------
            # Helper to stream logs from subprocess
            # -----------------------------
            def enqueue_output(out, queue):
                for line in iter(out.readline, ''):
                    queue.put(line)
                out.close()

            log_queue = queue.Queue()
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            t = threading.Thread(target=enqueue_output, args=(process.stdout, log_queue))
            t.daemon = True
            t.start()

            try:
                while True:
                    try:
                        line = log_queue.get(timeout=0.1)
                    except queue.Empty:
                        if process.poll() is not None:
                            break
                        else:
                            # Display frames dynamically above logs
                            if frames_dir.exists():
                                new_frames = []
                                for video_subdir in frames_dir.iterdir():
                                    for frame_file in sorted(video_subdir.glob("*.jpg")):
                                        if frame_file not in frames_displayed:
                                            frames_displayed.add(frame_file)
                                            new_frames.append(frame_file)
                                
                                if new_frames:
                                    with frames_container.container():
                                        st.subheader("🎯 Matching Frames")
                                        cols = st.columns(5)
                                        for i, frame_file in enumerate(new_frames):
                                            with cols[i % 5]:
                                                img = Image.open(frame_file)
                                                st.image(img, use_container_width=True, 
                                                       caption=f"Frame {frame_file.stem}")
                            continue

                    if line:
                        line = line.rstrip()
                        # Ignore tqdm frame lines
                        if not line.startswith("Processing frames:"):
                            logs.append(line)
                            log_text = "\n".join(logs[-50:])  # keep last 50 lines
                            # Update log box with scroll
                            logs_container.text_area(
                                label="📋 Processing Logs", 
                                value=log_text, 
                                height=300,
                                key=f"logs_box_{len(logs)}"  # unique key for each update
                            )

                    # Display frames dynamically above logs
                    if frames_dir.exists():
                        new_frames = []
                        for video_subdir in frames_dir.iterdir():
                            for frame_file in sorted(video_subdir.glob("*.jpg")):
                                if frame_file not in frames_displayed:
                                    frames_displayed.add(frame_file)
                                    new_frames.append(frame_file)
                        
                        if new_frames:
                            with frames_container.container():
                                st.subheader("🎯 Matching Frames")
                                cols = st.columns(5)
                                for i, frame_file in enumerate(new_frames):
                                    with cols[i % 5]:
                                        img = Image.open(frame_file)
                                        st.image(img, use_container_width=True,
                                               caption=f"Frame {frame_file.stem}")

                process.wait()

                if process.returncode == 0:
                    st.success("✅ Processing completed!")
                    # Add reset button after completion
                    if st.button("🔄 Process Another Video", type="primary"):
                        st.session_state.processing = False
                        st.rerun()
                else:
                    st.error("❌ VEENDER failed. Check logs above.")
                    if st.button("🔄 Try Again", type="primary"):
                        st.session_state.processing = False
                        st.rerun()

            except KeyboardInterrupt:
                process.send_signal(signal.SIGINT)
                st.warning("⚠️ Process interrupted by user.")
                st.session_state.processing = False

            finally:
                # Clean faces folder after run
                for old in face_dir.glob("*"):
                    old.unlink()
