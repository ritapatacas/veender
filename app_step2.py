import streamlit as st
from pathlib import Path
import subprocess
import tempfile
from PIL import Image
import os
import requests
import json
import cv2
import numpy as np
import time

st.set_page_config(page_title="VEENDER", page_icon="🎥", layout="wide")

st.markdown("<h1 style='text-align: center;'>VEENDER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; margin: 0;'>been there?</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; font-style: bold; margin: 0;'>self stalker - find yourself in a video</b></p>", unsafe_allow_html=True)

st.info("🔧 **Step 2**: Testing yt-dlp YouTube downloads + OpenCV video processing")

# Initialize session state for UI visibility
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Create containers for different states
input_container = st.container()
processing_container = st.container()

def test_opencv():
    """Test OpenCV functionality"""
    try:
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[:, :] = [255, 0, 0]  # Red image
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        return True, "OpenCV is working correctly"
    except Exception as e:
        return False, f"OpenCV error: {str(e)}"

def test_ytdlp():
    """Test yt-dlp availability"""
    try:
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, f"yt-dlp version: {version}"
        else:
            return False, "yt-dlp command failed"
    except FileNotFoundError:
        return False, "yt-dlp not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "yt-dlp version check timed out"
    except Exception as e:
        return False, f"yt-dlp test error: {str(e)}"

# Test components on app load
opencv_working, opencv_msg = test_opencv()
ytdlp_working, ytdlp_msg = test_ytdlp()

col1, col2 = st.columns(2)
with col1:
    if opencv_working:
        st.success(f"✅ {opencv_msg}")
    else:
        st.error(f"❌ {opencv_msg}")

with col2:
    if ytdlp_working:
        st.success(f"✅ {ytdlp_msg}")
    else:
        st.error(f"❌ {ytdlp_msg}")

# Only show interface if not processing
if not st.session_state.processing:
    with input_container:
        st.write("Upload face images and a YouTube link.")
        
        # Upload inputs
        face_files = st.file_uploader(
            "📸 Face images", 
            type=["jpg", "jpeg", "png"], 
            accept_multiple_files=True,
            help="Upload up to 5 reference face images"
        )
        
        if face_files and len(face_files) > 5:
            st.warning("⚠️ Maximum of 5 face images allowed.")
            face_files = face_files[:5]
        
        # YouTube URL input
        youtube_url = st.text_input("🎬 YouTube link", placeholder="https://youtube.com/watch?v=...")
        
        # Settings
        col1, col2 = st.columns(2)
        with col1:
            skip = st.slider("⏭️ Frame skip", min_value=1, max_value=200, value=30, help="Recommended: 10-50")
        with col2:
            tolerance = st.slider("🎯 Match tolerance", min_value=0.1, max_value=1.0, value=0.5, help="Recommended: 0.3-0.6")
        
        # Display uploaded images with OpenCV processing
        if face_files:
            st.subheader("📸 Uploaded Face Images (OpenCV processed):")
            cols = st.columns(min(5, len(face_files)))
            for i, face_file in enumerate(face_files):
                with cols[i]:
                    pil_img = Image.open(face_file)
                    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                    edges = cv2.Canny(gray, 50, 150)
                    processed_img = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
                    
                    st.image(pil_img, caption=f"Original: {face_file.name}", use_container_width=True)
                    st.image(processed_img, caption=f"Edges detected", use_container_width=True)
        
        # YouTube video info
        if youtube_url:
            st.subheader("📹 YouTube Video Info")
            try:
                if "youtube.com/watch?v=" in youtube_url:
                    video_id = youtube_url.split("v=")[1].split("&")[0]
                elif "youtu.be/" in youtube_url:
                    video_id = youtube_url.split("youtu.be/")[1].split("?")[0]
                else:
                    video_id = None
                
                if video_id:
                    st.info(f"🎬 Video ID: {video_id}")
                    st.success("✅ Valid YouTube URL detected")
                    
                    # Test yt-dlp info extraction
                    if st.button("🔍 Test Video Info Extraction", type="secondary"):
                        try:
                            with st.spinner("Extracting video info..."):
                                cmd = ["yt-dlp", "--dump-json", "--no-download", youtube_url]
                                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                                
                                if result.returncode == 0:
                                    info = json.loads(result.stdout)
                                    st.success("✅ Video info extracted successfully!")
                                    st.write(f"**Title**: {info.get('title', 'Unknown')}")
                                    st.write(f"**Duration**: {info.get('duration', 'Unknown')} seconds")
                                    st.write(f"**Uploader**: {info.get('uploader', 'Unknown')}")
                                else:
                                    st.error(f"❌ Failed to extract info: {result.stderr}")
                        except subprocess.TimeoutExpired:
                            st.error("❌ Video info extraction timed out")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                else:
                    st.error("❌ Invalid YouTube URL format")
            except:
                st.error("❌ Could not parse YouTube URL")
        
        # Run button
        if st.button("🚀 RUN VEENDER (Step 2 - Video Download Test)", type="primary", use_container_width=True):
            if not face_files:
                st.error("⚠️ Please upload at least one face image.")
            elif not youtube_url:
                st.error("⚠️ Please paste a YouTube link.")
            elif not ytdlp_working:
                st.error("⚠️ yt-dlp is not available. Cannot download videos.")
            else:
                st.session_state.processing = True
                st.session_state.face_files = face_files
                st.session_state.youtube_url = youtube_url
                st.session_state.skip = skip
                st.session_state.tolerance = tolerance
                st.rerun()

# Show processing interface when running
elif st.session_state.processing:
    with processing_container:
        st.info("🔄 Step 2 processing - Testing video download and basic frame extraction...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Process reference faces
            status_text.text("Processing reference faces with OpenCV...")
            progress_bar.progress(10)
            
            processed_count = 0
            for face_file in st.session_state.face_files:
                try:
                    pil_img = Image.open(face_file)
                    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    height, width, channels = cv_img.shape
                    st.success(f"✅ Processed: {face_file.name} ({width}x{height})")
                    processed_count += 1
                except Exception as e:
                    st.error(f"❌ Failed to process {face_file.name}: {e}")
            
            progress_bar.progress(30)
            
            # Download video
            status_text.text("Downloading video with yt-dlp...")
            with tempfile.TemporaryDirectory() as tmpdir:
                try:
                    # Use worst quality for faster download and testing
                    cmd = [
                        "yt-dlp",
                        "-f", "worst[ext=mp4]",
                        "-o", str(Path(tmpdir) / "video.%(ext)s"),
                        st.session_state.youtube_url
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    
                    if result.returncode == 0:
                        progress_bar.progress(60)
                        st.success("✅ Video downloaded successfully!")
                        
                        # Find downloaded video
                        video_files = list(Path(tmpdir).glob("video.*"))
                        if video_files:
                            video_path = video_files[0]
                            st.info(f"📁 Downloaded: {video_path.name}")
                            
                            # Test video processing with OpenCV
                            status_text.text("Testing video processing with OpenCV...")
                            progress_bar.progress(70)
                            
                            cap = cv2.VideoCapture(str(video_path))
                            if cap.isOpened():
                                fps = int(cap.get(cv2.CAP_PROP_FPS))
                                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                                duration = frame_count / fps if fps > 0 else 0
                                
                                st.success("✅ Video opened successfully with OpenCV!")
                                st.write(f"**Video Stats:**")
                                st.write(f"- Frames: {frame_count}")
                                st.write(f"- FPS: {fps}")
                                st.write(f"- Duration: {duration:.1f} seconds")
                                
                                # Extract a few sample frames
                                status_text.text("Extracting sample frames...")
                                progress_bar.progress(80)
                                
                                sample_frames = []
                                frame_positions = [0, frame_count // 4, frame_count // 2, frame_count * 3 // 4]
                                
                                for pos in frame_positions:
                                    cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
                                    ret, frame = cap.read()
                                    if ret:
                                        # Convert to RGB for display
                                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                        timestamp = pos / fps if fps > 0 else pos
                                        sample_frames.append((timestamp, frame_rgb))
                                
                                cap.release()
                                
                                if sample_frames:
                                    st.subheader("📺 Sample Frames Extracted:")
                                    cols = st.columns(len(sample_frames))
                                    for i, (timestamp, frame) in enumerate(sample_frames):
                                        with cols[i]:
                                            st.image(frame, caption=f"Frame at {timestamp:.1f}s", use_container_width=True)
                                
                                progress_bar.progress(100)
                                status_text.text("Step 2 completed successfully!")
                                
                                st.success("✅ Step 2 completed - Video download and processing working!")
                                st.info("🎯 **Next step**: Add face detection library (MediaPipe)")
                                
                            else:
                                st.error("❌ Could not open downloaded video with OpenCV")
                        else:
                            st.error("❌ No video file found after download")
                    else:
                        st.error(f"❌ Video download failed: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    st.error("❌ Video download timed out (5 minutes)")
                except Exception as e:
                    st.error(f"❌ Download error: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ Processing error: {str(e)}")
        
        finally:
            # Reset button
            if st.button("🔄 Test Another Video", type="primary"):
                st.session_state.processing = False
                st.rerun()

st.markdown("---")
st.markdown("**Step 2**: YouTube download + video processing test")
