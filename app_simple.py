import streamlit as st
from pathlib import Path
import tempfile
from PIL import Image
import os

st.set_page_config(page_title="VEENDER", page_icon="🎥", layout="wide")

st.markdown("<h1 style='text-align: center;'>VEENDER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; margin: 0;'>been there?</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; font-style: bold; margin: 0;'>self stalker - find yourself in a video</b></p>", unsafe_allow_html=True)

st.write("🚧 **Simplified version for deployment testing**")
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

# Mock processing button
if st.button("🚀 RUN VEENDER (Demo Mode)", type="primary", use_container_width=True):
    if not face_files:
        st.error("⚠️ Please upload at least one face image.")
    elif not youtube_url:
        st.error("⚠️ Please paste a YouTube link.")
    else:
        st.success("✅ App is working! Settings received:")
        st.write(f"- Face images: {len(face_files)} files")
        st.write(f"- YouTube URL: {youtube_url}")
        st.write(f"- Frame skip: {skip}")
        st.write(f"- Tolerance: {tolerance}")
        
        st.info("🔧 **Next step**: Add face recognition functionality once basic deployment works.")

st.markdown("---")
st.markdown("**Status**: Basic Streamlit app is running successfully!")
