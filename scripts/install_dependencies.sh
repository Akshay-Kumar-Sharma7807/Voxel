#!/bin/bash

# Voxel Ambient Art Generator - Dependency Installation Script
# This script automates the installation of system dependencies and Python packages

set -e  # Exit on any error

echo "🎨 Voxel Ambient Art Generator - Dependency Installation"
echo "======================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Raspberry Pi
check_raspberry_pi() {
    print_status "Checking if running on Raspberry Pi..."
    
    if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        print_success "Raspberry Pi detected"
        return 0
    else
        print_warning "Not running on Raspberry Pi - some features may not work optimally"
        return 1
    fi
}

# Update system packages
update_system() {
    print_status "Updating system packages..."
    
    sudo apt update
    sudo apt upgrade -y
    
    print_success "System packages updated"
}

# Install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    local packages=(
        "python3-pip"
        "python3-venv"
        "python3-dev"
        "git"
        "portaudio19-dev"
        "python3-pyaudio"
        "fbi"
        "alsa-utils"
        "pulseaudio"
        "pulseaudio-utils"
        "libasound2-dev"
        "libportaudio2"
        "libportaudiocpp0"
        "ffmpeg"
        "wget"
        "unzip"
        "curl"
    )
    
    for package in "${packages[@]}"; do
        print_status "Installing $package..."
        if sudo apt install -y "$package"; then
            print_success "$package installed"
        else
            print_error "Failed to install $package"
            exit 1
        fi
    done
    
    print_success "All system dependencies installed"
}

# Configure audio system
configure_audio() {
    print_status "Configuring audio system..."
    
    # Add user to audio group
    sudo usermod -a -G audio "$USER"
    
    # Start PulseAudio if not running
    if ! pgrep -x "pulseaudio" > /dev/null; then
        print_status "Starting PulseAudio..."
        pulseaudio --start
    fi
    
    # Test audio devices
    print_status "Available audio recording devices:"
    arecord -l || print_warning "No audio recording devices found"
    
    print_success "Audio system configured"
}

# Create Python virtual environment
create_venv() {
    print_status "Creating Python virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists, removing..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    print_success "Virtual environment created"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi
    
    source venv/bin/activate
    
    # Install requirements
    pip install -r requirements.txt
    
    print_success "Python dependencies installed"
}

# Download Vosk model
download_vosk_model() {
    print_status "Downloading Vosk speech recognition model..."
    
    # Create models directory
    mkdir -p models
    cd models
    
    # Check if model already exists
    if [ -d "vosk-model-en" ]; then
        print_warning "Vosk model already exists, skipping download"
        cd ..
        return 0
    fi
    
    # Download model
    local model_url="https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    local model_file="vosk-model-small-en-us-0.15.zip"
    
    print_status "Downloading model (91MB)..."
    if wget -O "$model_file" "$model_url"; then
        print_success "Model downloaded"
    else
        print_error "Failed to download Vosk model"
        cd ..
        exit 1
    fi
    
    # Extract model
    print_status "Extracting model..."
    unzip "$model_file"
    mv vosk-model-small-en-us-0.15 vosk-model-en
    
    # Clean up
    rm "$model_file"
    
    cd ..
    print_success "Vosk model installed"
}

# Create directories
create_directories() {
    print_status "Creating required directories..."
    
    local dirs=(
        "logs"
        "generated_images"
        "models"
        "scripts"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        print_status "Created directory: $dir"
    done
    
    print_success "Directories created"
}

# Create environment file template
create_env_template() {
    print_status "Creating environment file template..."
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Voxel Ambient Art Generator Configuration
# Copy this file and add your actual API key

# OpenAI API Key (required for image generation)
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Logging configuration
LOG_LEVEL=INFO
LOG_FILE=logs/voxel.log

# Optional: Audio configuration
AUDIO_SAMPLE_RATE=16000
AUDIO_CHUNK_DURATION=5

# Optional: Display configuration
DISPLAY_METHOD=fbi
DISPLAY_TIMEOUT=30
EOF
        print_success "Environment file template created (.env)"
        print_warning "Please edit .env and add your OpenAI API key"
    else
        print_warning ".env file already exists, skipping template creation"
    fi
}

# Test installation
test_installation() {
    print_status "Testing installation..."
    
    source venv/bin/activate
    
    # Test Python imports
    print_status "Testing Python imports..."
    python3 -c "
import sounddevice
import vosk
import openai
import pygame
print('All Python modules imported successfully')
" || {
        print_error "Python module import test failed"
        exit 1
    }
    
    # Test Vosk model
    print_status "Testing Vosk model..."
    if [ -d "models/vosk-model-en" ]; then
        print_success "Vosk model found"
    else
        print_error "Vosk model not found"
        exit 1
    fi
    
    # Test audio devices
    print_status "Testing audio devices..."
    python3 -c "
import sounddevice as sd
devices = sd.query_devices()
print(f'Found {len(devices)} audio devices')
" || print_warning "Audio device test failed - check microphone connection"
    
    print_success "Installation test completed"
}

# Main installation function
main() {
    echo
    print_status "Starting Voxel installation..."
    echo
    
    # Check if script is run from project directory
    if [ ! -f "requirements.txt" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Run installation steps
    check_raspberry_pi
    update_system
    install_system_deps
    configure_audio
    create_directories
    create_venv
    install_python_deps
    download_vosk_model
    create_env_template
    test_installation
    
    echo
    print_success "🎉 Installation completed successfully!"
    echo
    print_status "Next steps:"
    echo "1. Edit .env file and add your OpenAI API key"
    echo "2. Test the installation: python examples/test_audio_capture.py"
    echo "3. Run the application: python voxel.py"
    echo
    print_warning "Note: You may need to log out and back in for audio group changes to take effect"
}

# Run main function
main "$@"