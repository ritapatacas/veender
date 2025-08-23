import streamlit as st
from pathlib import Path
import tempfile
from PIL import Image
import os
import requests
import json
import cv2
import numpy as np

st.set_page_config(page_title="VEENDER", page_icon="🎥", layout="wide")

st.markdown("<h1 style='text-align: center;'>VEENDER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; margin: 0;'>been there?</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; font-style: bold; margin: 0;'>self stalker - find yourself in a video</b></p>", unsafe_allow_html=True)

st.info("🔧 **Step 1**: Testing OpenCV integration")

# Initialize session state for UI visibility
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Create containers for different states
input_container = st.container()
processing_container = st.container()

def test_opencv():
    """Test OpenCV functionality"""
    try:
        # Create a simple test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[:, :] = [255, 0, 0]  # Red image
        
        # Test basic OpenCV operations
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        return True, "OpenCV is working correctly"
    except Exception as e:
        return False, f"OpenCV error: {str(e)}"

# Test OpenCV on app load
opencv_working, opencv_msg = test_opencv()
if opencv_working:
    st.success(f"✅ {opencv_msg}")
else:
    st.error(f"❌ {opencv_msg}")

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
                    # Load image with PIL
                    pil_img = Image.open(face_file)
                    
                    # Convert to OpenCV format
                    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    
                    # Apply simple OpenCV processing (edge detection)
                    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                    edges = cv2.Canny(gray, 50, 150)
                    
                    # Convert back to display
                    processed_img = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
                    
                    # Display original and processed
                    st.image(pil_img, caption=f"Original: {face_file.name}", use_container_width=True)
                    st.image(processed_img, caption=f"Edges detected", use_container_width=True)
        
        # Mock YouTube video info
        if youtube_url:
            st.subheader("📹 YouTube Video Info")
            try:
                # Extract video ID
                if "youtube.com/watch?v=" in youtube_url:
                    video_id = youtube_url.split("v=")[1].split("&")[0]
                elif "youtu.be/" in youtube_url:
                    video_id = youtube_url.split("youtu.be/")[1].split("?")[0]
                else:
                    video_id = None
                
                if video_id:
                    st.info(f"🎬 Video ID: {video_id}")
                    st.success("✅ Valid YouTube URL detected")
                else:
                    st.error("❌ Invalid YouTube URL format")
            except:
                st.error("❌ Could not parse YouTube URL")
        
        # Test OpenCV video capabilities
        st.subheader("🔧 OpenCV Video Test")
        if st.button("Test OpenCV Video Capture", type="secondary"):
            try:
                # Test if OpenCV can create a VideoCapture object
                cap = cv2.VideoCapture()
                if cap is not None:
                    st.success("✅ OpenCV VideoCapture is available")
                    cap.release()
                else:
                    st.error("❌ OpenCV VideoCapture failed")
            except Exception as e:
                st.error(f"❌ OpenCV Video test failed: {e}")
        
        # Run button
        if st.button("🚀 RUN VEENDER (Step 1 - OpenCV Test)", type="primary", use_container_width=True):
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
        st.info("🔄 Step 1 processing mode - OpenCV testing...")
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        import time
        
        # Test OpenCV processing
        status_text.text("Testing OpenCV face image processing...")
        progress_bar.progress(20)
        time.sleep(1)
        
        processed_count = 0
        for i, face_file in enumerate(st.session_state.face_files):
            try:
                # Load and process with OpenCV
                pil_img = Image.open(face_file)
                cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                
                # Get image info
                height, width, channels = cv_img.shape
                
                st.success(f"✅ OpenCV processed: {face_file.name} ({width}x{height})")
                processed_count += 1
            except Exception as e:
                st.error(f"❌ Failed to process {face_file.name}: {e}")
        
        progress_bar.progress(60)
        status_text.text("Analyzing YouTube URL...")
        time.sleep(1)
        
        st.info(f"📹 Would process video: {st.session_state.youtube_url}")
        st.info(f"🔧 OpenCV successfully processed {processed_count}/{len(st.session_state.face_files)} face images")
        
        progress_bar.progress(100)
        status_text.text("Step 1 complete!")
        
        st.success("✅ Step 1 completed - OpenCV is working!")
        st.write("**Test Results:**")
        st.write(f"- Face images processed: {processed_count}/{len(st.session_state.face_files)}")
        st.write(f"- YouTube URL: {st.session_state.youtube_url}")
        st.write(f"- Frame skip: {st.session_state.skip}")
        st.write(f"- Tolerance: {st.session_state.tolerance}")
        
        st.info("🎯 **Next step**: Add yt-dlp for YouTube video downloads")
        
        # Reset button
        if st.button("🔄 Test Another Configuration", type="primary"):
            st.session_state.processing = False
            st.rerun()

st.markdown("---")
st.markdown("**Step 1**: OpenCV integration test - Building up functionality incrementally")
