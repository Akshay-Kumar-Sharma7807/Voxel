# Troubleshooting Guide

## Overview

This guide provides solutions for common issues encountered when running the Voxel ambient art generator. Issues are organized by component and include step-by-step resolution procedures.

## Quick Diagnostic Commands

Before diving into specific issues, run these commands to gather system information:

```bash
# System information
uname -a
cat /proc/cpuinfo | grep "Model"
vcgencmd measure_temp
vcgencmd get_throttled

# Audio system
arecord -l
pulseaudio --check -v

# Python environment
source venv/bin/activate
python --version
pip list | grep -E "(vosk|openai|sounddevice|pygame)"

# Application logs
tail -20 logs/voxel.log
tail -20 logs/errors.log
```

## Audio Issues

### Issue: Microphone Not Detected

**Symptoms:**
- "No audio input devices found" error
- Empty output from `arecord -l`
- Application fails to start audio capture

**Diagnosis:**
```bash
# Check USB devices
lsusb | grep -i audio

# Check kernel messages
dmesg | grep -i audio | tail -10

# Check ALSA devices
cat /proc/asound/cards
```

**Solutions:**

1. **Hardware Check:**
   ```bash
   # Try different USB port
   # Check USB cable integrity
   # Test microphone on another device
   ```

2. **Driver Installation:**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade
   
   # Install audio drivers
   sudo apt install alsa-utils pulseaudio-utils
   
   # Restart audio services
   sudo systemctl restart alsa-state
   ```

3. **Permissions Fix:**
   ```bash
   # Add user to audio group
   sudo usermod -a -G audio $USER
   
   # Log out and back in, then test
   groups | grep audio
   ```

### Issue: Poor Audio Quality

**Symptoms:**
- Low volume in recordings
- Background noise/static
- Intermittent audio capture

**Diagnosis:**
```bash
# Test recording quality
arecord -d 5 -f cd test.wav
aplay test.wav

# Check audio levels
alsamixer
```

**Solutions:**

1. **Adjust Audio Levels:**
   ```bash
   # Open ALSA mixer
   alsamixer
   
   # Select capture device (F4)
   # Adjust input gain
   # Save settings: sudo alsactl store
   ```

2. **Microphone Positioning:**
   - Move microphone closer to conversation area
   - Avoid reflective surfaces
   - Check for electromagnetic interference

3. **PulseAudio Configuration:**
   ```bash
   # Edit PulseAudio config
   nano ~/.config/pulse/default.pa
   
   # Add line for noise cancellation:
   # load-module module-echo-cancel
   
   # Restart PulseAudio
   pulseaudio --kill && pulseaudio --start
   ```

### Issue: Audio Capture Timeout

**Symptoms:**
- "Audio capture timeout" errors
- Intermittent audio processing
- Long delays between captures

**Solutions:**

1. **Check System Load:**
   ```bash
   htop
   iostat 1 5
   ```

2. **Optimize Audio Buffer:**
   ```bash
   # Edit audio configuration in voxel/config.py
   # Increase buffer size or adjust chunk duration
   ```

3. **USB Power Issues:**
   ```bash
   # Check USB power
   lsusb -v | grep -i power
   
   # Add to /boot/config.txt:
   # max_usb_current=1
   ```

## Speech Recognition Issues

### Issue: Vosk Model Not Found

**Symptoms:**
- "Model not found" error on startup
- Speech recognition initialization fails
- FileNotFoundError for model path

**Diagnosis:**
```bash
# Check model directory
ls -la models/
ls -la models/vosk-model-en/

# Verify model structure
find models/vosk-model-en -name "*.json" -o -name "*.fst"
```

**Solutions:**

1. **Re-download Model:**
   ```bash
   cd models
   rm -rf vosk-model-en
   wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
   unzip vosk-model-small-en-us-0.15.zip
   mv vosk-model-small-en-us-0.15 vosk-model-en
   rm vosk-model-small-en-us-0.15.zip
   ```

2. **Check Permissions:**
   ```bash
   chmod -R 755 models/vosk-model-en
   ```

3. **Verify Model Integrity:**
   ```bash
   # Test model loading
   python3 -c "
   import vosk
   model = vosk.Model('models/vosk-model-en')
   print('Model loaded successfully')
   "
   ```

### Issue: Low Speech Recognition Accuracy

**Symptoms:**
- Incorrect transcriptions
- Empty transcription results
- Low confidence scores

**Solutions:**

1. **Improve Audio Quality:**
   - Check microphone positioning
   - Reduce background noise
   - Adjust input levels

2. **Model Configuration:**
   ```python
   # In speech processor, adjust recognition settings
   rec = vosk.KaldiRecognizer(model, 16000)
   rec.SetMaxAlternatives(3)  # Get multiple alternatives
   rec.SetWords(True)  # Enable word-level timestamps
   ```

3. **Alternative Model:**
   ```bash
   # Download larger model for better accuracy
   cd models
   wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
   # Note: Larger model requires more memory
   ```

## API Integration Issues

### Issue: Freepik API Authentication Failed

**Symptoms:**
- "Invalid API key" errors
- 401 Unauthorized responses
- Image generation fails with Freepik provider

**Diagnosis:**
```bash
# Check environment variables
echo $FREEPIK_API_KEY
cat .env | grep FREEPIK

# Test API manually
curl -H "X-Freepik-API-Key: $FREEPIK_API_KEY" \
     https://api.freepik.com/v1/ai/text-to-image
```

**Solutions:**

1. **Verify API Key Format:**
   ```bash
   # Check .env file
   cat .env | grep FREEPIK
   
   # Key should start with 'FPSX' and be ~32 characters
   # Example: FPSX1234567890abcdef1234567890abcd
   ```

2. **Check Provider Setting:**
   ```bash
   # Ensure IMAGE_PROVIDER is set to freepik
   grep IMAGE_PROVIDER .env
   # Should show: IMAGE_PROVIDER=freepik
   ```

3. **Test API Access:**
   ```bash
   # Test with curl
   curl -X POST \
        -H "X-Freepik-API-Key: YOUR_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"prompt": "test image"}' \
        https://api.freepik.com/v1/ai/text-to-image
   ```

### Issue: OpenAI API Authentication Failed

**Symptoms:**
- "Invalid API key" errors
- 401 Unauthorized responses
- Image generation fails immediately

**Diagnosis:**
```bash
# Check environment variables
echo $OPENAI_API_KEY
cat .env | grep OPENAI

# Test API manually
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

**Solutions:**

1. **Verify API Key:**
   ```bash
   # Check .env file
   cat .env
   
   # Ensure no extra spaces or quotes
   # Key should start with 'sk-'
   ```

2. **Environment Loading:**
   ```bash
   # Test environment loading
   python3 -c "
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print('API Key loaded:', bool(os.getenv('OPENAI_API_KEY')))
   "
   ```

3. **API Key Validation:**
   ```bash
   # Test with curl
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://api.openai.com/v1/models | jq .
   ```

### Issue: Wrong Image Provider Selected

**Symptoms:**
- Using wrong API (e.g., OpenAI when Freepik intended)
- Unexpected costs or API errors
- Different image quality than expected

**Diagnosis:**
```bash
# Check current provider setting
grep IMAGE_PROVIDER .env

# Check what provider the app is using
python3 -c "
from voxel.config import GenerationConfig
print('Current provider:', GenerationConfig.PROVIDER)
"
```

**Solutions:**

1. **Set Correct Provider:**
   ```bash
   # Edit .env file
   nano .env
   
   # Set to desired provider:
   # IMAGE_PROVIDER=freepik    (recommended)
   # IMAGE_PROVIDER=openai     (higher cost)
   # IMAGE_PROVIDER=google_cloud (requires GCP setup)
   ```

2. **Verify API Keys Match Provider:**
   ```bash
   # For Freepik
   grep -E "(IMAGE_PROVIDER|FREEPIK_API_KEY)" .env
   
   # For OpenAI
   grep -E "(IMAGE_PROVIDER|OPENAI_API_KEY)" .env
   ```

3. **Test Provider Switch:**
   ```bash
   # Test image generation with specific provider
   python examples/test_image_generator.py
   ```

### Issue: API Rate Limiting

**Symptoms:**
- "Rate limit exceeded" errors
- 429 HTTP status codes
- Long delays in image generation

**Solutions:**

1. **Check Rate Limits:**
   ```bash
   # Monitor API usage in OpenAI dashboard
   # Check current tier limits
   ```

2. **Implement Backoff:**
   ```python
   # In image generator, add exponential backoff
   import time
   import random
   
   def retry_with_backoff(func, max_retries=3):
       for attempt in range(max_retries):
           try:
               return func()
           except RateLimitError:
               wait_time = (2 ** attempt) + random.uniform(0, 1)
               time.sleep(wait_time)
       raise
   ```

3. **Adjust Timing:**
   ```bash
   # Increase cooldown period in config
   # Reduce frequency of API calls
   ```

### Issue: Network Connectivity Problems

**Symptoms:**
- Connection timeout errors
- Intermittent API failures
- DNS resolution issues

**Diagnosis:**
```bash
# Test connectivity
ping api.openai.com
nslookup api.openai.com
curl -I https://api.openai.com

# Check network configuration
ip route show
cat /etc/resolv.conf
```

**Solutions:**

1. **Network Configuration:**
   ```bash
   # Use Google DNS
   echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf
   
   # Restart networking
   sudo systemctl restart networking
   ```

2. **Proxy Configuration:**
   ```bash
   # If behind proxy, set environment variables
   export https_proxy=http://proxy:port
   export http_proxy=http://proxy:port
   ```

## Display Issues

### Issue: Images Not Displaying

**Symptoms:**
- Black screen after image generation
- "Display command failed" errors
- Images generated but not shown

**Diagnosis:**
```bash
# Test display manually
fbi -T 1 generated_images/test_image.png

# Check framebuffer
ls -la /dev/fb*

# Test pygame display
python3 -c "
import pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
print('Pygame display initialized')
"
```

**Solutions:**

1. **FBI Display Issues:**
   ```bash
   # Install FBI if missing
   sudo apt install fbi
   
   # Check framebuffer permissions
   sudo chmod 666 /dev/fb0
   
   # Test with different terminal
   sudo fbi -T 1 -a image.png
   ```

2. **Pygame Fallback:**
   ```bash
   # Install pygame dependencies
   sudo apt install python3-pygame
   
   # Test fullscreen mode
   export SDL_VIDEODRIVER=fbcon
   export SDL_FBDEV=/dev/fb0
   ```

3. **HDMI Configuration:**
   ```bash
   # Edit /boot/config.txt
   sudo nano /boot/config.txt
   
   # Add/modify:
   hdmi_force_hotplug=1
   hdmi_group=1
   hdmi_mode=16
   ```

### Issue: Display Resolution Problems

**Symptoms:**
- Images appear stretched or cropped
- Wrong aspect ratio
- Overscan issues

**Solutions:**

1. **Resolution Detection:**
   ```bash
   # Get current resolution
   fbset
   
   # Or using xrandr (if X11 running)
   xrandr
   ```

2. **Manual Resolution Setting:**
   ```bash
   # In /boot/config.txt
   hdmi_group=2
   hdmi_mode=82  # 1920x1080
   disable_overscan=1
   ```

3. **Image Preprocessing:**
   ```python
   # Adjust image scaling in display controller
   from PIL import Image
   
   def resize_image(image_path, target_size):
       img = Image.open(image_path)
       img = img.resize(target_size, Image.LANCZOS)
       return img
   ```

## Performance Issues

### Issue: High CPU Usage

**Symptoms:**
- System sluggish
- High temperature warnings
- Throttling messages

**Diagnosis:**
```bash
# Monitor CPU usage
htop
iostat 1 5

# Check temperature and throttling
vcgencmd measure_temp
vcgencmd get_throttled

# Check running processes
ps aux --sort=-%cpu | head -10
```

**Solutions:**

1. **Process Optimization:**
   ```bash
   # Kill unnecessary processes
   sudo systemctl disable bluetooth
   sudo systemctl stop bluetooth
   
   # Adjust CPU governor
   echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   ```

2. **Cooling Improvements:**
   ```bash
   # Check current temperature
   vcgencmd measure_temp
   
   # Add cooling solutions:
   # - Heat sinks
   # - Cooling fan
   # - Better case ventilation
   ```

3. **Code Optimization:**
   ```python
   # Optimize audio processing
   # Reduce model complexity
   # Implement caching where possible
   ```

### Issue: Memory Issues

**Symptoms:**
- Out of memory errors
- System freezing
- High swap usage

**Diagnosis:**
```bash
# Check memory usage
free -h
cat /proc/meminfo

# Monitor memory over time
watch -n 1 free -h
```

**Solutions:**

1. **Increase Swap:**
   ```bash
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile
   # Set CONF_SWAPSIZE=2048
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

2. **Memory Optimization:**
   ```bash
   # Reduce GPU memory if not needed
   # In /boot/config.txt:
   gpu_mem=64
   ```

3. **Code Memory Management:**
   ```python
   # Implement proper cleanup
   import gc
   
   def cleanup_resources():
       gc.collect()
       # Clear audio buffers
       # Remove old images
   ```

## Application-Specific Issues

### Issue: Application Won't Start

**Symptoms:**
- Import errors on startup
- Configuration file not found
- Permission denied errors

**Diagnosis:**
```bash
# Check Python environment
source venv/bin/activate
python --version
pip list

# Test imports
python3 -c "
import voxel
print('Voxel module imported successfully')
"

# Check file permissions
ls -la voxel.py
ls -la .env
```

**Solutions:**

1. **Environment Issues:**
   ```bash
   # Recreate virtual environment
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration Issues:**
   ```bash
   # Check configuration files
   cp .env.example .env
   nano .env  # Add API key
   ```

3. **Permission Issues:**
   ```bash
   # Fix file permissions
   chmod +x voxel.py
   chmod 644 .env
   ```

### Issue: Continuous Loop Errors

**Symptoms:**
- Application stops after first cycle
- Repeated error messages
- Graceful shutdown not working

**Solutions:**

1. **Error Handling:**
   ```python
   # Improve error handling in main loop
   try:
       # Main processing
       pass
   except Exception as e:
       logger.error(f"Cycle error: {e}")
       continue  # Don't break the loop
   ```

2. **Signal Handling:**
   ```python
   import signal
   
   def signal_handler(sig, frame):
       logger.info("Graceful shutdown initiated")
       cleanup_and_exit()
   
   signal.signal(signal.SIGINT, signal_handler)
   ```

## Log Analysis

### Understanding Log Messages

**Common Log Patterns:**

1. **Audio Issues:**
   ```
   ERROR: Audio capture failed: [Errno -9981] Input overflowed
   Solution: Reduce audio buffer size or increase processing speed
   ```

2. **API Issues:**
   ```
   ERROR: OpenAI API error: Rate limit exceeded
   Solution: Implement backoff strategy or reduce request frequency
   ```

3. **Display Issues:**
   ```
   ERROR: Display command failed: fbi: can't open '/dev/fb0'
   Solution: Check framebuffer permissions and HDMI connection
   ```

### Log File Locations

```bash
# Application logs
tail -f logs/voxel.log

# Error logs
tail -f logs/errors.log

# System logs
sudo journalctl -u voxel-service -f

# Audio system logs
journalctl -u pulseaudio -f
```

## Getting Help

### Information to Collect

When seeking help, collect this information:

```bash
#!/bin/bash
# System information collection script

echo "=== Voxel Troubleshooting Information ==="
echo "Date: $(date)"
echo "System: $(uname -a)"
echo "Raspberry Pi Model: $(cat /proc/cpuinfo | grep Model)"
echo "Temperature: $(vcgencmd measure_temp)"
echo "Throttling: $(vcgencmd get_throttled)"
echo "Memory: $(free -h | grep Mem)"
echo "Disk: $(df -h / | tail -1)"
echo ""
echo "=== Audio Devices ==="
arecord -l
echo ""
echo "=== Python Environment ==="
source venv/bin/activate
python --version
pip list | grep -E "(vosk|openai|sounddevice|pygame)"
echo ""
echo "=== Recent Errors ==="
tail -20 logs/errors.log
echo ""
echo "=== Configuration ==="
cat .env | sed 's/OPENAI_API_KEY=.*/OPENAI_API_KEY=***HIDDEN***/'
```

### Support Resources

1. **Project Documentation:**
   - README.md
   - INSTALLATION.md
   - HARDWARE_SETUP.md

2. **Community Support:**
   - GitHub Issues
   - Project discussions
   - Raspberry Pi forums

3. **Component Documentation:**
   - Vosk documentation
   - OpenAI API documentation
   - Raspberry Pi documentation

### Emergency Recovery

If the system becomes completely unresponsive:

1. **Safe Shutdown:**
   ```bash
   sudo shutdown -h now
   ```

2. **SD Card Recovery:**
   - Remove SD card
   - Mount on another computer
   - Check file system integrity
   - Restore from backup if needed

3. **Fresh Installation:**
   - Re-flash Raspberry Pi OS
   - Run installation script
   - Restore configuration from backup

This troubleshooting guide should help resolve most common issues encountered with the Voxel ambient art generator.