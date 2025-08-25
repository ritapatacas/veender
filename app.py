import streamlit as st
import subprocess
import tempfile
from pathlib import Path
from PIL import Image

st.set_page_config(page_title="YouTube Frame Extractor (FFmpeg)", page_icon="🎥", layout="wide")
st.title("YouTube Frame Extractor (FFmpeg Version)")

youtube_url = st.text_input("YouTube link", placeholder="https://youtube.com/watch?v=...")

if st.button("🎬 Extract 10 Frames"):
    if not youtube_url:
        st.error("⚠️ Please provide a YouTube link.")
    else:
        st.info("Fetching video and extracting frames using ffmpeg...")
        try:
            # Create a temporary directory to store frames
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)

                # Command: yt-dlp + ffmpeg directly extract 10 frames (1 per second)
                # First, get the direct URL
                cmd_url = ["yt-dlp", "-g", "-f", "worst[ext=mp4]", youtube_url]
                result = subprocess.run(cmd_url, capture_output=True, text=True, timeout=60)
                if result.returncode != 0:
                    st.error(f"❌ Failed to get video URL: {result.stderr}")
                    st.stop()

                direct_url = result.stdout.strip()
                st.write("Direct video URL obtained.")

                # Now extract 10 frames with ffmpeg at 1 fps
                output_pattern = str(tmp_path / "frame_%03d.jpg")
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-i", direct_url,
                    "-vf", "fps=1,select=lt(n\,10)",  # 1 fps, limit to first 10 frames
                    "-vsync", "vfr",
                    "-q:v", "2",
                    output_pattern
                ]

                ffmpeg_res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=120)
                if ffmpeg_res.returncode != 0:
                    st.error(f"❌ ffmpeg failed: {ffmpeg_res.stderr}")
                    st.stop()

                frames = sorted(tmp_path.glob("frame_*.jpg"))
                if not frames:
                    st.warning("No frames were extracted. Possibly a protected or inaccessible stream.")
                else:
                    st.success(f"Extracted {len(frames)} frames!")
                    cols = st.columns(min(5, len(frames)))
                    for i, frame_file in enumerate(frames):
                        img = Image.open(frame_file)
                        with cols[i % 5]:
                            st.image(img, caption=f"Frame {i+1}", use_container_width=True)

        except subprocess.TimeoutExpired:
            st.error("❌ Operation timed out.")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

st.markdown("---")
st.markdown("**Powered by yt-dlp + ffmpeg**")
