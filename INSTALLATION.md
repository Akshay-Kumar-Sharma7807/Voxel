# Voxel Ambient Art Generator - Installation Guide

## Overview

This guide will help you set up the Voxel ambient art generator on a Raspberry Pi. The system requires specific hardware configuration and software dependencies to function properly.

## Hardware Requirements

### Minimum Requirements
- Raspberry Pi 4 Model B (4GB RAM recommended)
- MicroSD card (32GB or larger, Class 10)
- USB microphone (compatible with Linux audio drivers)
- HDMI monitor or display
- Stable internet connection for image generation API calls

### Recommended Hardware
- Raspberry Pi 4 Model B with 8GB RAM
- High-quality USB microphone with noise cancellation
- 1080p HDMI monitor for optimal image display
- Ethernet connection for stable internet

## Software Prerequisites

### Operating System
- Raspberry Pi OS (64-bit) - Latest version
- Desktop environment enabled for display functionality

## Installation Steps

### 1. Prepare Raspberry Pi OS

First, ensure your Raspberry Pi OS is up to date:

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install System Dependencies

Install required system packages:

```bash
sudo apt install -y \
    python3-pip \
    python3-venv \
    git \
    portaudio19-dev \
    python3-pyaudio \
    fbi \
    alsa-utils \
    pulseaudio \
    pulseaudio-utils
```

### 3. Configure Audio System

Enable and configure audio services:

```bash
# Start PulseAudio
pulseaudio --start

# Test audio recording (optional)
arecord -l  # List available recording devices
```

### 4. Clone and Setup Project

Clone the repository and set up the Python environment:

```bash
# Clone the project
git clone <repository-url> voxel-art-generator
cd voxel-art-generator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 5. Download Vosk Speech Model

The system uses the Vosk speech recognition model for on-device processing:

```bash
# Create models directory
mkdir -p models

# Download the English model (91MB)
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip

# Extract the model
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 vosk-model-en

# Clean up
rm vosk-model-small-en-us-0.15.zip
cd ..
```

### 6. Configure Environment Variables

Create a `.env` file with your API keys:

```bash
# Create environment file from template
cp .env.example .env

# Edit the file and add your API keys
nano .env
```

Add the following content to `.env`:
```
# Choose your image generation provider
IMAGE_PROVIDER=freepik  # Options: openai, google_cloud, freepik

# Freepik API (recommended - affordable and high quality)
FREEPIK_API_KEY=your_freepik_api_key_here

# OpenAI API (alternative)
OPENAI_API_KEY=your_openai_api_key_here

# Google Cloud (alternative - requires additional setup)
GCP_PROJECT_ID=your_project_id
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

**Recommended Setup: Freepik API**
- Most cost-effective option
- High-quality image generation
- Multiple styles and models available
- See [FREEPIK_SETUP.md](FREEPIK_SETUP.md) for detailed setup instructions

### 7. Test Installation

Run the test suite to verify everything is working:

```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Run tests
python -m pytest tests/ -v
```

### 8. Test Audio Capture

Test your microphone setup:

```bash
# Test audio capture
python examples/test_audio_capture.py
```

### 9. Run the Application

Start the Voxel ambient art generator:

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python voxel.py
```

## Configuration

### Audio Configuration

If you encounter audio issues, check the following:

1. **List audio devices:**
   ```bash
   arecord -l
   ```

2. **Set default audio device:**
   ```bash
   # Edit ALSA configuration
   sudo nano /etc/asound.conf
   ```

3. **Test microphone:**
   ```bash
   # Record a 5-second test
   arecord -d 5 -f cd test.wav
   aplay test.wav
   ```

### Display Configuration

For optimal display performance:

1. **Enable GPU memory split:**
   ```bash
   sudo raspi-config
   # Navigate to Advanced Options > Memory Split
   # Set to 128 or 256
   ```

2. **Configure HDMI output:**
   ```bash
   sudo nano /boot/config.txt
   # Ensure these lines are present:
   # hdmi_force_hotplug=1
   # hdmi_group=1
   # hdmi_mode=16  # 1080p 60Hz
   ```

## Troubleshooting

### Common Issues

#### Audio Not Working
- **Problem:** No audio input detected
- **Solution:** 
  ```bash
  # Check if microphone is detected
  lsusb | grep -i audio
  
  # Restart audio services
  sudo systemctl restart alsa-state
  pulseaudio --kill
  pulseaudio --start
  ```

#### Vosk Model Not Found
- **Problem:** Speech recognition fails to initialize
- **Solution:**
  ```bash
  # Verify model path
  ls -la models/vosk-model-en/
  
  # Re-download if necessary
  cd models && rm -rf vosk-model-en
  # Follow step 5 again
  ```

#### Display Issues
- **Problem:** Images not displaying fullscreen
- **Solution:**
  ```bash
  # Test FBI display
  fbi -T 1 generated_images/test_image.png
  
  # If FBI fails, check framebuffer
  ls -la /dev/fb*
  
  # Enable framebuffer if needed
  sudo modprobe fb
  ```

#### API Connection Issues
- **Problem:** DALL-E 3 API calls failing
- **Solution:**
  ```bash
  # Test internet connectivity
  ping api.openai.com
  
  # Verify API key
  echo $OPENAI_API_KEY
  
  # Test API manually
  python examples/test_image_generator.py
  ```

#### Memory Issues
- **Problem:** System running out of memory
- **Solution:**
  ```bash
  # Increase swap space
  sudo dphys-swapfile swapoff
  sudo nano /etc/dphys-swapfile
  # Set CONF_SWAPSIZE=2048
  sudo dphys-swapfile setup
  sudo dphys-swapfile swapon
  ```

### Performance Optimization

For better performance on Raspberry Pi:

1. **Disable unnecessary services:**
   ```bash
   sudo systemctl disable bluetooth
   sudo systemctl disable wifi-powersave
   ```

2. **Optimize GPU memory:**
   ```bash
   # In /boot/config.txt
   gpu_mem=128
   ```

3. **Use faster SD card:**
   - Use Class 10 or better microSD card
   - Consider USB 3.0 storage for better I/O

### Log Files

Check log files for debugging:

```bash
# Application logs
tail -f logs/voxel.log

# Error logs
tail -f logs/errors.log

# System logs
sudo journalctl -u voxel-service -f
```

## Automatic Startup (Optional)

To run Voxel automatically on boot:

1. **Create systemd service:**
   ```bash
   sudo nano /etc/systemd/system/voxel.service
   ```

2. **Add service configuration:**
   ```ini
   [Unit]
   Description=Voxel Ambient Art Generator
   After=network.target sound.target
   
   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/voxel-art-generator
   Environment=PATH=/home/pi/voxel-art-generator/venv/bin
   ExecStart=/home/pi/voxel-art-generator/venv/bin/python voxel.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable voxel.service
   sudo systemctl start voxel.service
   ```

## Security Considerations

- Keep your OpenAI API key secure and never commit it to version control
- Regularly update the system and dependencies
- Consider firewall configuration if running on a network
- Monitor API usage to avoid unexpected charges

## Additional Documentation

For comprehensive setup and troubleshooting information, refer to these additional guides:

- **[Hardware Setup Guide](HARDWARE_SETUP.md)** - Detailed hardware configuration and optimization
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Solutions for common issues and problems
- **[Models Documentation](models/README.md)** - Vosk model installation and configuration
- **[Freepik Setup](FREEPIK_SETUP.md)** - Alternative image generation setup
- **[Google Cloud Setup](GOOGLE_CLOUD_SETUP.md)** - Cloud-based deployment options

## Automated Installation Scripts

For easier installation, use the provided scripts:

```bash
# Complete dependency installation (Linux/Raspberry Pi)
./scripts/install_dependencies.sh

# Vosk model setup only
./scripts/setup_vosk_model.sh

# Windows setup guidance
scripts/install_dependencies.bat
```

## Support

If you encounter issues not covered in this guide:

1. **Check Documentation:**
   - Review the troubleshooting guide
   - Check hardware setup requirements
   - Verify model installation

2. **Diagnostic Information:**
   - Check log files: `tail -f logs/voxel.log`
   - Run system diagnostics
   - Test individual components using example scripts

3. **Community Support:**
   - Check the project's issue tracker
   - Review existing issues and solutions
   - Create a new issue with diagnostic information

4. **Hardware Issues:**
   - Consult the Raspberry Pi documentation
   - Check community forums for hardware-specific problems
   - Verify all connections are secure

For the most up-to-date information and community support, visit the project repository.