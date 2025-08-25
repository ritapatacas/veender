# app.py
import streamlit as st
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
import base64
import tempfile

NGROK_URL = "https://cda17b462672.ngrok-free.app/process_video"

st.set_page_config(page_title="VEENDER", page_icon="🎥", layout="wide")

st.markdown("<h1 style='text-align: center;'>VEENDER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; margin: 0;'>been there?</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; font-style: bold; margin: 0;'>self stalker - find yourself in a video</b></p>", unsafe_allow_html=True)

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False

input_container = st.container()
processing_container = st.container()

if not st.session_state.processing:
    with input_container:
        st.write("Upload face images and a YouTube link.")

        # Upload faces
        face_files = st.file_uploader(
            "📸 Face images",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="Upload up to 5 reference face images"
        )
        if face_files and len(face_files) > 5:
            st.warning("⚠️ Maximum of 5 face images allowed.")
            face_files = face_files[:5]

        # YouTube URL
        youtube_url = st.text_input("🎬 YouTube link", placeholder="https://youtube.com/watch?v=...")

        # Sliders
        col1, col2 = st.columns(2)
        with col1:
            skip = st.slider("⏭️ Frame skip", min_value=1, max_value=200, value=30)
        with col2:
            tolerance = st.slider("🎯 Match tolerance", min_value=0.1, max_value=1.0, value=0.5)

        if st.button("🚀 RUN VEENDER"):
            if not face_files:
                st.error("⚠️ Please upload at least one face image.")
            elif not youtube_url:
                st.error("⚠️ Please paste a YouTube link.")
            else:
                st.session_state.processing = True
                st.session_state.face_files = face_files
                st.session_state.youtube_url = youtube_url
                st.session_state.skip = skip
                st.session_state.tolerance = tolerance
                st.rerun()

elif st.session_state.processing:
    with processing_container:
        st.info("🔄 Sending data to backend...")

        # Prepare files and payload
        files_payload = []
        for f in st.session_state.face_files:
            files_payload.append(('faces', (f.name, f.read(), f.type)))

        payload = {
            'url': st.session_state.youtube_url,
            'skip': st.session_state.skip,
            'tolerance': st.session_state.tolerance
        }

        try:
            response = requests.post(NGROK_URL, data=payload, files=files_payload, timeout=600)
            data = response.json()

            if "error" in data:
                st.error(f"❌ Backend error: {data['error']}")
            else:
                st.success(f"✅ {data['message']}")
                frames = data["frames"]
                cols = st.columns(5)
                for i, frame_b64 in enumerate(frames):
                    img = Image.open(BytesIO(base64.b64decode(frame_b64)))
                    with cols[i % 5]:
                        st.image(img, use_container_width=True, caption=f"Frame {i+1}")

        except Exception as e:
            st.error(f"❌ Request failed: {e}")

        if st.button("🔄 Process Another Video"):
            st.session_state.processing = False
            st.rerun()
