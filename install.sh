#!/bin/bash
set -e

echo "🚀 VEENDER - Quick Installer"
echo "============================="

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION+ is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create and activate virtual environment
echo "📦 Setting up virtual environment..."
python3 -m venv veender_env
source veender_env/bin/activate

# Install veender
echo "⬇️ Installing VEENDER..."
pip install --upgrade pip
pip install veender  # Once published to PyPI

# Create sample directories
echo "📁 Creating sample directories..."
mkdir -p data/input/{face,videos}
mkdir -p data/output/{frames,logs}

# Create default config if it doesn't exist
if [ ! -f "config.yaml" ]; then
    echo "⚙️ Creating default config..."
    cat > config.yaml << EOF
# VEENDER Configuration
frame_skip: 30
tolerance: 0.5
output_dir: "data/output"
faces_dir: "data/input/face"
videos_dir: "data/input/videos"
EOF
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📋 Quick start:"
echo "   1. Add face photos to: data/input/face/"
echo "   2. Add videos to: data/input/videos/"
echo "   3. Run: veender --video path/to/video.mp4"
echo "   4. Or try YouTube: veender --yt 'https://youtube.com/watch?v=VIDEO_ID'"
echo ""
echo "💡 To activate environment later: source veender_env/bin/activate"
echo "💡 To deactivate: deactivate"
echo ""
echo "🎯 VEENDER is now installed and ready to use!"

```

