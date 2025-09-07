@echo off
REM Voxel Ambient Art Generator - Windows Dependency Installation Script
REM This script provides guidance for Windows users

echo.
echo 🎨 Voxel Ambient Art Generator - Windows Setup Guide
echo ===================================================
echo.
echo This project is designed to run on Raspberry Pi with Linux.
echo For Windows development/testing, follow these steps:
echo.
echo 1. Install Python 3.8 or later from python.org
echo 2. Install Git from git-scm.com
echo 3. Open Command Prompt or PowerShell as Administrator
echo.
echo 4. Clone the repository:
echo    git clone ^<repository-url^> voxel-art-generator
echo    cd voxel-art-generator
echo.
echo 5. Create virtual environment:
echo    python -m venv venv
echo    venv\Scripts\activate
echo.
echo 6. Install Python dependencies:
echo    pip install -r requirements.txt
echo.
echo 7. Download Vosk model:
echo    mkdir models
echo    cd models
echo    curl -L -o vosk-model-small-en-us-0.15.zip https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
echo    tar -xf vosk-model-small-en-us-0.15.zip
echo    ren vosk-model-small-en-us-0.15 vosk-model-en
echo    del vosk-model-small-en-us-0.15.zip
echo    cd ..
echo.
echo 8. Create .env file:
echo    copy .env.example .env
echo    notepad .env
echo    ^(Add your OpenAI API key^)
echo.
echo 9. Test the installation:
echo    python examples\test_speech_processor.py
echo.
echo Note: Some features may not work on Windows:
echo - FBI framebuffer display ^(Linux only^)
echo - Audio device handling may differ
echo - Performance may vary
echo.
echo For production deployment, use Raspberry Pi with Raspberry Pi OS.
echo.
pause