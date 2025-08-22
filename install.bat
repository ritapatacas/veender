@echo off
setlocal enabledelayedexpansion

echo 🚀 VEENDER - Quick Installer
echo ============================

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed.
    pause
    exit /b 1
)

echo ✅ Python detected

:: Create and activate virtual environment
echo 📦 Setting up virtual environment...
python -m venv veender_env
call veender_env\Scripts\activate.bat

:: Install veender
echo ⬇️ Installing VEENDER...
python -m pip install --upgrade pip
pip install veender

:: Create sample directories
echo 📁 Creating sample directories...
mkdir data\input\face 2>nul
mkdir data\input\videos 2>nul
mkdir data\output\frames 2>nul
mkdir data\output\logs 2>nul

:: Create default config if it doesn't exist
if not exist config.yaml (
    echo ⚙️ Creating default config...
    echo # VEENDER Configuration > config.yaml
    echo frame_skip: 30 >> config.yaml
    echo tolerance: 0.5 >> config.yaml
    echo output_dir: "data/output" >> config.yaml
    echo faces_dir: "data/input/face" >> config.yaml
    echo videos_dir: "data/input/videos" >> config.yaml
)

echo.
echo 🎉 Installation complete!
echo.
echo 📋 Quick start:
echo    1. Add face photos to: data\input\face\
echo    2. Add videos to: data\input\videos\
echo    3. Run: veender --video path\to\video.mp4
echo    4. Or try YouTube: veender --yt "https://youtube.com/watch?v=VIDEO_ID"
echo.
echo 💡 To activate environment later: veender_env\Scripts\activate.bat
echo 💡 To deactivate: deactivate
echo.
echo 🎯 VEENDER is now installed and ready to use!

pause
