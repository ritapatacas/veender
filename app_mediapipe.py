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
import cv2
import numpy as np
import mediapipe as mp
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="VEENDER", page_icon="🎥", layout="wide")

st.markdown("<h1 style='text-align: center;'>VEENDER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; margin: 0;'>been there?</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; font-style: bold; margin: 0;'>self stalker - find yourself in a video</b></p>", unsafe_allow_html=True)

# Initialize MediaPipe
@st.cache_resource
def init_mediapipe():
    mp_face_detection = mp.solutions.face_detection
    mp_face_mesh = mp.solutions.face_mesh
    return mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5), mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5)

face_detection, face_mesh = init_mediapipe()

def extract_face_features(image):
    """Extract face features using MediaPipe"""
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_image)
    
    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0]
        # Extract key facial landmarks as features
        features = []
        for landmark in landmarks.landmark[:468]:  # 468 landmarks
            features.extend([landmark.x, landmark.y, landmark.z])
        return np.array(features)
    return None

def compare_faces(ref_features, target_features, threshold=0.7):
    """Compare faces using cosine similarity"""
    if ref_features is None or target_features is None:
        return False
    
    similarity = cosine_similarity([ref_features], [target_features])[0][0]
    return similarity > threshold

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
        
        # Upload inputs - Compact Layout
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
        
        # Side-by-side sliders
        col1, col2 = st.columns(2)
        with col1:
            skip = st.slider("⏭️ Frame skip", min_value=1, max_value=200, value=30, help="Recommended: 10-50")
        with col2:
            tolerance = st.slider("🎯 Match tolerance", min_value=0.3, max_value=0.9, value=0.7, help="Recommended: 0.6-0.8")
        
        # Display uploaded images
        if face_files:
            st.subheader("📸 Uploaded Face Images:")
            cols = st.columns(min(5, len(face_files)))
            for i, face_file in enumerate(face_files):
                with cols[i]:
                    img = Image.open(face_file)
                    st.image(img, caption=face_file.name, use_container_width=True)
        
        # Run VEENDER
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

# Show processing interface when running
elif st.session_state.processing:
    with processing_container:
        st.info("🔄 Processing with MediaPipe face detection...")
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Process reference faces
            status_text.text("Loading reference faces...")
            ref_features_list = []
            
            for i, face_file in enumerate(st.session_state.face_files):
                # Convert PIL to cv2
                pil_image = Image.open(face_file)
                cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                
                features = extract_face_features(cv_image)
                if features is not None:
                    ref_features_list.append(features)
                    st.success(f"✅ Processed reference face: {face_file.name}")
                else:
                    st.warning(f"⚠️ No face detected in: {face_file.name}")
            
            if not ref_features_list:
                st.error("❌ No faces detected in uploaded images!")
                if st.button("🔄 Try Again", type="primary"):
                    st.session_state.processing = False
                    st.rerun()
                st.stop()
            
            # Average reference features
            ref_features = np.mean(ref_features_list, axis=0)
            progress_bar.progress(20)
            
            # Download video
            status_text.text("Downloading video...")
            with tempfile.TemporaryDirectory() as tmpdir:
                try:
                    cmd = [
                        "yt-dlp",
                        "-f", "worst[ext=mp4]",  # Use worst quality for faster processing
                        "-o", str(Path(tmpdir) / "video.%(ext)s"),
                        st.session_state.youtube_url
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    if result.returncode != 0:
                        st.error(f"❌ Failed to download video: {result.stderr}")
                        if st.button("🔄 Try Again", type="primary"):
                            st.session_state.processing = False
                            st.rerun()
                        st.stop()
                    
                    # Find downloaded video
                    video_files = list(Path(tmpdir).glob("video.*"))
                    if not video_files:
                        st.error("❌ No video file found after download")
                        if st.button("🔄 Try Again", type="primary"):
                            st.session_state.processing = False
                            st.rerun()
                        st.stop()
                    
                    video_path = video_files[0]
                    progress_bar.progress(40)
                    
                    # Process video
                    status_text.text("Processing video frames...")
                    cap = cv2.VideoCapture(str(video_path))
                    
                    if not cap.isOpened():
                        st.error("❌ Could not open video file")
                        if st.button("🔄 Try Again", type="primary"):
                            st.session_state.processing = False
                            st.rerun()
                        st.stop()
                    
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    
                    st.info(f"📹 Video info: {frame_count} frames, {fps} FPS")
                    
                    matches = []
                    frame_container = st.container()
                    
                    frame_number = 0
                    processed_frames = 0
                    total_frames_to_process = frame_count // st.session_state.skip
                    
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        
                        if frame_number % st.session_state.skip == 0:
                            # Extract features from current frame
                            frame_features = extract_face_features(frame)
                            
                            if frame_features is not None:
                                # Compare with reference
                                if compare_faces(ref_features, frame_features, st.session_state.tolerance):
                                    timestamp = frame_number / fps
                                    matches.append((timestamp, frame))
                                    
                                    # Display match
                                    with frame_container:
                                        st.success(f"🎯 Match found at {timestamp:.1f}s!")
                                        col1, col2 = st.columns([1, 3])
                                        with col1:
                                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                            st.image(frame_rgb, caption=f"Frame at {timestamp:.1f}s", use_container_width=True)
                            
                            processed_frames += 1
                            progress = 40 + (processed_frames / total_frames_to_process) * 50
                            progress_bar.progress(min(90, int(progress)))
                            status_text.text(f"Processed {processed_frames}/{total_frames_to_process} frames...")
                        
                        frame_number += 1
                    
                    cap.release()
                    progress_bar.progress(100)
                    
                    # Show results
                    if matches:
                        st.success(f"✅ Found {len(matches)} matches!")
                        
                        # Display all matches
                        st.subheader("🎯 All Matching Frames")
                        cols = st.columns(min(4, len(matches)))
                        for i, (timestamp, frame) in enumerate(matches):
                            with cols[i % 4]:
                                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                st.image(frame_rgb, caption=f"{timestamp:.1f}s", use_container_width=True)
                    else:
                        st.warning("⚠️ No matches found. Try adjusting the tolerance or using different reference images.")
                    
                except subprocess.TimeoutExpired:
                    st.error("❌ Video download timed out (5 minutes). Try a shorter video.")
                except Exception as e:
                    st.error(f"❌ Processing error: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
        
        finally:
            # Reset button
            if st.button("🔄 Process Another Video", type="primary"):
                st.session_state.processing = False
                st.rerun()

st.markdown("---")
st.markdown("**Powered by MediaPipe** - Cloud-friendly face detection")
