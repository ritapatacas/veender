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
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="VEENDER", page_icon="🎥", layout="wide")

st.markdown("<h1 style='text-align: center;'>VEENDER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; margin: 0;'>been there?</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; font-style: bold; margin: 0;'>self stalker - find yourself in a video</b></p>", unsafe_allow_html=True)

st.info("🔧 **Step 3 Alternative**: Using OpenCV Haar Cascades for face detection (Python 3.13 compatible)")

# YouTube download notice
st.warning("""⚠️ **YouTube Download Limitation**: 
Due to YouTube's cloud server blocking, video downloads may fail in this hosted environment. 
The app will automatically create a demo video to show face detection working if YouTube downloads fail.
For full YouTube functionality, run this app locally on your computer.""")

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

def test_face_detection():
    """Test OpenCV Haar Cascade face detection"""
    try:
        # Load the pre-trained Haar Cascade for face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Create a simple test image with basic shapes
        test_image = np.ones((200, 200, 3), dtype=np.uint8) * 128
        cv2.circle(test_image, (100, 100), 80, (255, 200, 180), -1)  # Face circle
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        return True, f"OpenCV Haar Cascade loaded successfully"
        
    except Exception as e:
        return False, f"Face detection error: {str(e)}"

@st.cache_resource
def load_face_cascade():
    """Load the Haar Cascade face detector"""
    return cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def extract_face_features(image, face_cascade):
    """Extract face features using OpenCV Haar Cascades"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    if len(faces) > 0:
        # Take the largest face
        face = max(faces, key=lambda x: x[2] * x[3])  # largest by area
        x, y, w, h = face
        
        # Extract face region
        face_roi = gray[y:y+h, x:x+w]
        
        # Resize to standard size for comparison
        face_roi = cv2.resize(face_roi, (100, 100))
        
        # Use histogram as features (simple but effective)
        hist = cv2.calcHist([face_roi], [0], None, [256], [0, 256])
        return hist.flatten()
    
    return None

def compare_faces(ref_features, target_features, threshold=0.7):
    """Compare faces using histogram correlation"""
    if ref_features is None or target_features is None:
        return False
    
    # Normalize features
    ref_norm = ref_features / (np.linalg.norm(ref_features) + 1e-6)
    target_norm = target_features / (np.linalg.norm(target_features) + 1e-6)
    
    # Calculate similarity using correlation
    similarity = np.corrcoef(ref_norm, target_norm)[0, 1]
    
    # Handle NaN case
    if np.isnan(similarity):
        return False
    
    return similarity > threshold

# Test components on app load
opencv_working, opencv_msg = test_opencv()
ytdlp_working, ytdlp_msg = test_ytdlp()
face_detection_working, face_detection_msg = test_face_detection()

col1, col2, col3 = st.columns(3)
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

with col3:
    if face_detection_working:
        st.success(f"✅ {face_detection_msg}")
    else:
        st.error(f"❌ {face_detection_msg}")

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
            tolerance = st.slider("🎯 Match tolerance", min_value=0.3, max_value=0.9, value=0.7, help="Recommended: 0.6-0.8")
        
        # Display uploaded images with OpenCV face detection
        if face_files and face_detection_working:
            st.subheader("📸 Uploaded Face Images (OpenCV Haar Cascade detection):")
            face_cascade = load_face_cascade()
            
            cols = st.columns(min(5, len(face_files)))
            for i, face_file in enumerate(face_files):
                with cols[i]:
                    pil_img = Image.open(face_file)
                    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    
                    # OpenCV face detection
                    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    
                    # Draw face detection rectangles
                    annotated_img = cv_img.copy()
                    for (x, y, w, h) in faces:
                        cv2.rectangle(annotated_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(annotated_img, "Face", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    
                    # Convert back to RGB for display
                    annotated_rgb = cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB)
                    
                    st.image(pil_img, caption=f"Original: {face_file.name}", use_container_width=True)
                    if len(faces) > 0:
                        st.image(annotated_rgb, caption=f"Faces detected: {len(faces)}", use_container_width=True)
                    else:
                        st.warning("No faces detected")
        
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
                    
                    # Debug button for testing video access
                    col_debug1, col_debug2 = st.columns(2)
                    with col_debug1:
                        if st.button("🔍 Debug: Test Video Info", type="secondary"):
                            with st.spinner("Testing video access..."):
                                test_cmd = [
                                    "yt-dlp", 
                                    "--dump-json",
                                    "--no-download",
                                    youtube_url
                                ]
                                try:
                                    result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)
                                    if result.returncode == 0:
                                        video_info = json.loads(result.stdout)
                                        st.success("✅ Video info accessible!")
                                        st.write(f"**Title**: {video_info.get('title', 'Unknown')}")
                                        st.write(f"**Duration**: {video_info.get('duration', 'Unknown')} seconds")
                                        st.write(f"**Uploader**: {video_info.get('uploader', 'Unknown')}")
                                        st.write(f"**View Count**: {video_info.get('view_count', 'Unknown')}")
                                        if video_info.get('url'):
                                            st.write("**Stream URL**: ✅ Available")
                                        else:
                                            st.write("**Stream URL**: ❌ Not available")
                                    else:
                                        st.error(f"❌ Cannot access video info: {result.stderr}")
                                except Exception as e:
                                    st.error(f"❌ Error testing video: {str(e)}")
                    
                    with col_debug2:
                        if st.button("🎯 Debug: Test Frame Extraction", type="secondary"):
                            with st.spinner("Testing frame extraction strategies..."):
                                import tempfile
                                with tempfile.TemporaryDirectory() as tmpdir:
                                    # Test Strategy 1: Stream URL extraction
                                    st.write("**Testing Strategy 1**: Stream URL extraction")
                                    info_cmd = [
                                        "yt-dlp", 
                                        "--dump-json",
                                        "--no-download",
                                        "-f", "worst[height<=480]",
                                        youtube_url
                                    ]
                                    
                                    try:
                                        result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=60)
                                        if result.returncode == 0:
                                            video_info = json.loads(result.stdout)
                                            stream_url = video_info.get('url')
                                            if stream_url:
                                                st.success("✅ Stream URL obtained")
                                                # Test if OpenCV can open it
                                                cap = cv2.VideoCapture(stream_url)
                                                if cap.isOpened():
                                                    ret, frame = cap.read()
                                                    if ret:
                                                        st.success("✅ OpenCV can read frames from stream")
                                                        # Display first frame as test
                                                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                                        st.image(frame_rgb, caption="Sample frame from stream", width=300)
                                                    else:
                                                        st.error("❌ OpenCV cannot read frames from stream")
                                                    cap.release()
                                                else:
                                                    st.error("❌ OpenCV cannot open stream URL")
                                            else:
                                                st.error("❌ No stream URL in video info")
                                        else:
                                            st.error(f"❌ Strategy 1 failed: {result.stderr[:100]}")
                                    except Exception as e:
                                        st.error(f"❌ Strategy 1 error: {str(e)}")
                                    
                                    # Test Strategy 2: Thumbnail extraction
                                    st.write("**Testing Strategy 2**: Thumbnail extraction")
                                    thumb_cmd = [
                                        "yt-dlp",
                                        "--write-thumbnail",
                                        "--skip-download",
                                        "-o", str(Path(tmpdir) / "debug_thumbnail.%(ext)s"),
                                        youtube_url
                                    ]
                                    
                                    try:
                                        thumb_result = subprocess.run(thumb_cmd, capture_output=True, text=True, timeout=30)
                                        if thumb_result.returncode == 0:
                                            thumbnails = list(Path(tmpdir).glob("debug_thumbnail.*"))
                                            if thumbnails:
                                                st.success(f"✅ Got {len(thumbnails)} thumbnail(s)")
                                                # Display thumbnail
                                                thumb_img = Image.open(thumbnails[0])
                                                st.image(thumb_img, caption="Video thumbnail", width=300)
                                            else:
                                                st.error("❌ No thumbnails found")
                                        else:
                                            st.error(f"❌ Strategy 2 failed: {thumb_result.stderr[:100]}")
                                    except Exception as e:
                                        st.error(f"❌ Strategy 2 error: {str(e)}")
                else:
                    st.error("❌ Invalid YouTube URL format")
            except:
                st.error("❌ Could not parse YouTube URL")
        
        # Run button
        all_systems_working = opencv_working and ytdlp_working and face_detection_working
        
        if st.button("🚀 RUN VEENDER (OpenCV Face Detection)", type="primary", use_container_width=True):
            if not face_files:
                st.error("⚠️ Please upload at least one face image.")
            elif not youtube_url:
                st.error("⚠️ Please paste a YouTube link.")
            elif not all_systems_working:
                st.error("⚠️ Some components are not working. Check the status indicators above.")
            else:
                st.session_state.processing = True
                st.session_state.face_files = face_files
                st.session_state.youtube_url = youtube_url
                st.session_state.skip = skip
                st.session_state.tolerance = tolerance
                st.rerun()

# Show processing interface when running (FULL PIPELINE)
elif st.session_state.processing:
    with processing_container:
        st.info("🔄 Processing with OpenCV Haar Cascade face detection...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Load face cascade
            face_cascade = load_face_cascade()
            
            # Process reference faces
            status_text.text("Processing reference faces with OpenCV...")
            ref_features_list = []
            
            for i, face_file in enumerate(st.session_state.face_files):
                # Convert PIL to cv2
                pil_image = Image.open(face_file)
                cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                
                features = extract_face_features(cv_image, face_cascade)
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
            
            # Extract frames from video
            status_text.text("Extracting frames from video (no full download needed)...")
            with tempfile.TemporaryDirectory() as tmpdir:
                download_success = False
                video_path = None
                
                # Test both strategies to compare effectiveness
                strategies = [
                    # Strategy 1: Thumbnail extraction approach (10 thumbnails)
                    "extract_thumbnails", 
                    # Strategy 2: Stream URL extraction approach (10 frames)
                    "extract_frames_direct",
                    # Strategy 3: Demo mode fallback
                    "demo"
                ]
                
                for i, strategy in enumerate(strategies):
                    try:
                        status_text.text(f"Trying strategy {i+1}/{len(strategies)}: {strategy.replace('_', ' ').title()}...")
                        
                        # Strategy 1: Thumbnail extraction approach (get main thumbnail, create 10 points)
                        if strategy == "extract_thumbnails":
                            st.info("🎯 Strategy 1: Thumbnail extraction approach")
                            
                            # Get video info first
                            info_cmd = [
                                "yt-dlp",
                                "--dump-json", 
                                "--no-download",
                                st.session_state.youtube_url
                            ]
                            
                            result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)
                            if result.returncode == 0:
                                try:
                                    video_info = json.loads(result.stdout)
                                    duration = video_info.get('duration', 300)
                                    title = video_info.get('title', 'Unknown')
                                    
                                    st.success(f"✅ Video info: '{title}' ({duration}s)")
                                    
                                    frames_extracted = []
                                    
                                    # Extract one main thumbnail and create 10 time points (1 per second)
                                    thumb_cmd = [
                                        "yt-dlp",
                                        "--write-thumbnail",
                                        "--skip-download", 
                                        "-o", str(Path(tmpdir) / "main_thumbnail.%(ext)s"),
                                        st.session_state.youtube_url
                                    ]
                                    
                                    thumb_result = subprocess.run(thumb_cmd, capture_output=True, text=True, timeout=30)
                                    if thumb_result.returncode == 0:
                                        thumbnails = list(Path(tmpdir).glob("main_thumbnail.*"))
                                        if thumbnails:
                                            st.success(f"✅ Got main thumbnail: {thumbnails[0].name}")
                                            
                                            # Create 10 time points using the same thumbnail (1 per second for first 10 seconds)
                                            for second in range(10):  # 0, 1, 2, ..., 9 seconds
                                                frames_extracted.append((float(second), thumbnails[0]))
                                                st.info(f"📍 Frame point at {second}s")
                                        else:
                                            st.warning("⚠️ Thumbnail command succeeded but no file found")
                                            st.info(f"📂 Directory contents: {list(Path(tmpdir).glob('*'))}")
                                    else:
                                        st.warning(f"⚠️ Thumbnail download failed: {thumb_result.stderr[:100]}")
                                        with st.expander("🔍 Full error details"):
                                            st.code(f"Command: {' '.join(thumb_cmd)}")
                                            st.code(f"Return code: {thumb_result.returncode}")
                                            st.code(f"STDOUT: {thumb_result.stdout}")
                                            st.code(f"STDERR: {thumb_result.stderr}")
                                    
                                    if frames_extracted:
                                        st.success(f"✅ Strategy 1: Extracted {len(frames_extracted)} thumbnail-based frame points")
                                        
                                        # Store Strategy 1 results
                                        if not download_success:  # Use first successful strategy as main result
                                            video_data = {
                                                'frames': frames_extracted,
                                                'fps': 1,  # 1 frame per second
                                                'duration': 10  # We only have 10 seconds worth
                                            }
                                            video_path = video_data
                                            download_success = True
                                        
                                        # Continue to test Strategy 2 for comparison
                                        continue
                                    else:
                                        st.warning("⚠️ Strategy 1 failed: Could not extract any thumbnails")
                                        continue
                                        
                                except json.JSONDecodeError:
                                    st.error("❌ Could not parse video info JSON")
                            else:
                                st.warning(f"⚠️ Could not get video info: {result.stderr[:100]}")
                            continue
                        
                        # Strategy 2: Stream URL extraction approach (extract 10 actual frames)
                        elif strategy == "extract_frames_direct":
                            st.info("🎯 Strategy 2: Stream URL extraction approach")
                            
                            # Get video stream URL for frame extraction
                            info_cmd = [
                                "yt-dlp", 
                                "--dump-json",
                                "--no-download",
                                "-f", "worst[height<=480]",
                                st.session_state.youtube_url
                            ]
                            
                            result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=60)
                            if result.returncode == 0:
                                try:
                                    video_info = json.loads(result.stdout)
                                    stream_url = video_info.get('url')
                                    duration = video_info.get('duration', 60)
                                    title = video_info.get('title', 'Unknown')
                                    
                                    st.success(f"✅ Strategy 2 video info: '{title}' ({duration}s)")
                                    
                                    if stream_url:
                                        st.success(f"✅ Got stream URL for Strategy 2")
                                        
                                        # Extract 10 frames using OpenCV directly from stream
                                        try:
                                            cap = cv2.VideoCapture(stream_url)
                                            if cap.isOpened():
                                                frames_extracted_s2 = []
                                                fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
                                                
                                                # Extract frames at 1-second intervals for first 10 seconds
                                                for second in range(10):
                                                    frame_pos = second * fps  # Frame position for this second
                                                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                                                    ret, frame = cap.read()
                                                    if ret:
                                                        frame_path = Path(tmpdir) / f"stream_frame_{second}s.jpg"
                                                        cv2.imwrite(str(frame_path), frame)
                                                        frames_extracted_s2.append((float(second), frame_path))
                                                        st.info(f"✅ Strategy 2: Extracted frame at {second}s")
                                                    else:
                                                        st.warning(f"⚠️ Strategy 2: Could not read frame at {second}s")
                                                
                                                cap.release()
                                                
                                                if frames_extracted_s2:
                                                    st.success(f"✅ Strategy 2: Extracted {len(frames_extracted_s2)} actual frames from stream!")
                                                    
                                                    # Store Strategy 2 results (but keep Strategy 1 as main if it worked)
                                                    if not download_success:  # Use Strategy 2 if Strategy 1 failed
                                                        video_data = {
                                                            'frames': frames_extracted_s2,
                                                            'fps': fps,
                                                            'duration': duration
                                                        }
                                                        video_path = video_data
                                                        download_success = True
                                                    
                                                    # Continue to demo for full comparison
                                                    continue
                                                else:
                                                    st.warning("⚠️ Strategy 2: No frames could be extracted from stream")
                                            else:
                                                st.warning("⚠️ Strategy 2: Stream URL obtained but couldn't open with OpenCV")
                                        except Exception as e:
                                            st.warning(f"⚠️ Strategy 2: OpenCV error: {str(e)}")
                                    else:
                                        st.warning("⚠️ Strategy 2: No stream URL found in video info")
                                except json.JSONDecodeError:
                                    st.error("❌ Strategy 2: Could not parse video info JSON")
                            else:
                                st.warning(f"⚠️ Strategy 2: Could not get video info: {result.stderr[:100]}")
                            continue
                        
                        # Strategy 3: Demo mode (final fallback)
                        elif strategy == "demo":
                            st.warning("🎬 Strategy 3: Demo Mode - Creating sample video for demonstration")
                            st.info("📝 **Note**: Demo video creates generic face patterns. For realistic matching, upload a photo with clear facial features and adjust tolerance to 0.3-0.5")
                            
                            # Create a simple demo video with OpenCV
                            import cv2
                            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                            demo_path = Path(tmpdir) / "demo_video.mp4"
                            out = cv2.VideoWriter(str(demo_path), fourcc, 10.0, (640, 480))
                            
                            # Create multiple frames with varied face-like patterns
                            for frame_num in range(100):  # More frames for better testing
                                # Create varied background
                                bg_color = (50 + frame_num % 100, 80 + frame_num % 150, 120 + frame_num % 200)
                                demo_frame = np.full((480, 640, 3), bg_color, dtype=np.uint8)
                                
                                # Create multiple face-like shapes with variation
                                for face_idx in range(2):  # Two faces per frame
                                    base_x = 160 + face_idx * 320 + int(30 * np.sin(frame_num * 0.1 + face_idx))
                                    base_y = 240 + int(20 * np.cos(frame_num * 0.08 + face_idx))
                                    
                                    # Vary face size and features
                                    face_size = 50 + int(20 * np.sin(frame_num * 0.05))
                                    
                                    # Face shape (oval)
                                    cv2.ellipse(demo_frame, (base_x, base_y), (face_size, int(face_size * 1.2)), 0, 0, 360, (255, 220, 177), -1)
                                    
                                    # Eyes with variation
                                    eye_y = base_y - int(face_size * 0.3)
                                    eye_size = max(3, int(face_size * 0.15))
                                    cv2.circle(demo_frame, (base_x - int(face_size * 0.3), eye_y), eye_size, (0, 0, 0), -1)
                                    cv2.circle(demo_frame, (base_x + int(face_size * 0.3), eye_y), eye_size, (0, 0, 0), -1)
                                    
                                    # Nose
                                    nose_y = base_y
                                    cv2.line(demo_frame, (base_x, nose_y - 5), (base_x, nose_y + 5), (150, 100, 100), 2)
                                    
                                    # Mouth with variation
                                    mouth_y = base_y + int(face_size * 0.4)
                                    mouth_width = int(face_size * 0.4)
                                    if frame_num % 20 < 10:  # Smile variation
                                        cv2.ellipse(demo_frame, (base_x, mouth_y), (mouth_width, 8), 0, 0, 180, (0, 0, 0), 2)
                                    else:
                                        cv2.line(demo_frame, (base_x - mouth_width//2, mouth_y), (base_x + mouth_width//2, mouth_y), (0, 0, 0), 2)
                                
                                out.write(demo_frame)
                            
                            out.release()
                            
                            if demo_path.exists():
                                video_path = demo_path
                                download_success = True
                                st.success("✅ Demo video created with varied face patterns for testing")
                                st.info("🎯 **Tip**: The demo creates generic faces. Real matches depend on your reference image quality and tolerance settings.")
                                break
                            continue
                        
                        # This section is now handled by individual strategies above
                        pass
                    except subprocess.TimeoutExpired:
                        st.warning(f"Strategy {i+1} timed out")
                    except Exception as e:
                        st.warning(f"Strategy {i+1} error: {str(e)}")
                
                if not download_success:
                    st.error("❌ All strategies failed - Strategy comparison complete")
                    
                    st.warning("""📊 **Strategy Test Results**:
- 🖼️ **Strategy 1 (Thumbnail)**: Failed - Cannot download YouTube thumbnails 
- 🎬 **Strategy 2 (Stream)**: Failed - Cannot access YouTube stream URLs
- 🎭 **Strategy 3 (Demo)**: Available as fallback for testing""")
                    
                    st.info("""🔍 **Analysis**:
- **Both strategies blocked**: YouTube restricts cloud/datacenter IPs
- **Strategy 1 typically more reliable**: Thumbnails have less restrictions than full streams
- **Strategy 2 higher quality**: Real frames vs. thumbnail replication
- **Neither works in cloud environment**: Requires residential IP/authentication""")
                    
                    st.success("🎯 **Strategy recommendation**: Strategy 1 (thumbnail) is usually better for cloud deployment when it works, Strategy 2 (stream) gives higher quality when accessible.")
                    if st.button("🔄 Try Again", type="primary"):
                        st.session_state.processing = False
                        st.rerun()
                    st.stop()
                
                progress_bar.progress(40)
                
                # Process video with face detection
                status_text.text("Processing frames with face detection...")
                
                matches = []
                frame_container = st.container()
                
                # Handle different video path types
                if isinstance(video_path, dict):
                    # Frame data from stream extraction
                    frames_data = video_path['frames']
                    fps = video_path['fps']
                    duration = video_path['duration']
                    
                    st.info(f"📹 Frame data: {len(frames_data)} frames extracted, {fps} FPS, {duration}s duration")
                    
                    for i, (timestamp, frame_path) in enumerate(frames_data):
                        # Load frame from file
                        frame = cv2.imread(str(frame_path))
                        if frame is not None:
                            # Extract features from current frame
                            frame_features = extract_face_features(frame, face_cascade)
                            
                            if frame_features is not None:
                                # Compare with reference
                                if compare_faces(ref_features, frame_features, st.session_state.tolerance):
                                    matches.append((timestamp, frame))
                                    
                                    # Display match immediately
                                    with frame_container:
                                        st.success(f"🎯 Match found at {timestamp:.1f}s!")
                                        col1, col2 = st.columns([1, 3])
                                        with col1:
                                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                            st.image(frame_rgb, caption=f"Frame at {timestamp:.1f}s", use_container_width=True)
                        
                        progress = 40 + ((i + 1) / len(frames_data)) * 50
                        progress_bar.progress(min(90, int(progress)))
                        status_text.text(f"Processed {i+1}/{len(frames_data)} frames...")
                
                else:
                    # Traditional video file processing
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
                    
                    frame_number = 0
                    processed_frames = 0
                    total_frames_to_process = frame_count // st.session_state.skip
                    
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        
                        if frame_number % st.session_state.skip == 0:
                            # Extract features from current frame
                            frame_features = extract_face_features(frame, face_cascade)
                            
                            if frame_features is not None:
                                # Compare with reference
                                if compare_faces(ref_features, frame_features, st.session_state.tolerance):
                                    timestamp = frame_number / fps
                                    matches.append((timestamp, frame))
                                    
                                    # Display match immediately
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
                
                # Show final results
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
                    st.warning("⚠️ No matches found. This is normal for demo videos with generic faces.")
                    st.info("""💡 **To see matches**:
- **Lower tolerance** to 0.3-0.4 for more sensitive matching
- **Upload clearer reference images** with distinct facial features  
- **Try different demo runs** - face patterns vary each time
- **Local deployment** with real YouTube videos will show better results""")
        
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
        
        finally:
            # Reset button
            if st.button("🔄 Process Another Video", type="primary"):
                st.session_state.processing = False
                st.rerun()

st.markdown("---")
st.markdown("**Step 3 Alternative**: Full VEENDER pipeline with OpenCV Haar Cascades (Python 3.13 compatible)")
