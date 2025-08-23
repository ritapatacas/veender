import streamlit as st
from pathlib import Path
import tempfile
from PIL import Image
import os
import requests
import json

st.set_page_config(page_title="VEENDER", page_icon="🎥", layout="wide")

st.markdown("<h1 style='text-align: center;'>VEENDER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; margin: 0;'>been there?</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; font-style: bold; margin: 0;'>self stalker - find yourself in a video</b></p>", unsafe_allow_html=True)

st.info("🔧 **Minimal Version**: Testing deployment with basic dependencies only")

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
        
        # Display uploaded images
        if face_files:
            st.subheader("📸 Uploaded Face Images:")
            cols = st.columns(min(5, len(face_files)))
            for i, face_file in enumerate(face_files):
                with cols[i]:
                    img = Image.open(face_file)
                    st.image(img, caption=face_file.name, use_container_width=True)
        
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
        
        # Run button
        if st.button("🚀 RUN VEENDER (Demo Mode)", type="primary", use_container_width=True):
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
        st.info("🔄 Demo processing mode...")
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        import time
        
        # Simulate processing steps
        status_text.text("Loading reference faces...")
        progress_bar.progress(20)
        time.sleep(1)
        
        for i, face_file in enumerate(st.session_state.face_files):
            st.success(f"✅ Processed reference face: {face_file.name}")
        
        status_text.text("Analyzing YouTube URL...")
        progress_bar.progress(40)
        time.sleep(1)
        
        st.info(f"📹 Would download: {st.session_state.youtube_url}")
        
        status_text.text("Simulating video processing...")
        progress_bar.progress(60)
        time.sleep(2)
        
        status_text.text("Generating mock results...")
        progress_bar.progress(80)
        time.sleep(1)
        
        # Mock results
        progress_bar.progress(100)
        status_text.text("Processing complete!")
        
        st.success("✅ Demo processing completed!")
        st.write("**Settings used:**")
        st.write(f"- Face images: {len(st.session_state.face_files)} files")
        st.write(f"- YouTube URL: {st.session_state.youtube_url}")
        st.write(f"- Frame skip: {st.session_state.skip}")
        st.write(f"- Tolerance: {st.session_state.tolerance}")
        
        st.info("🔧 **Next step**: Add video processing libraries once basic deployment is stable.")
        
        # Reset button
        if st.button("🔄 Process Another Video", type="primary"):
            st.session_state.processing = False
            st.rerun()

st.markdown("---")
st.markdown("**Deployment Test Version** - Minimal dependencies for reliable cloud deployment")
