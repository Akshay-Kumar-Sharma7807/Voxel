# Hardware Setup Guide

## Overview

This guide covers the physical hardware setup and configuration for the Voxel ambient art generator. Proper hardware setup is crucial for optimal performance and reliability.

## Required Hardware Components

### Core Components

1. **Raspberry Pi 4 Model B**
   - **Minimum:** 4GB RAM
   - **Recommended:** 8GB RAM for better performance
   - **Alternative:** Raspberry Pi 5 (when available)

2. **MicroSD Card**
   - **Minimum:** 32GB Class 10
   - **Recommended:** 64GB Class 10 or better
   - **Alternative:** USB 3.0 SSD for better I/O performance

3. **USB Microphone**
   - **Requirements:** Linux-compatible, USB Audio Class compliant
   - **Recommended models:**
     - Blue Yeti Nano
     - Audio-Technica ATR2100x-USB
     - Samson Go Mic
     - Any USB microphone with good noise cancellation

4. **HDMI Display**
   - **Minimum:** 1080p (1920x1080) resolution
   - **Recommended:** Any size monitor or TV with HDMI input
   - **Note:** Display will show fullscreen ambient art

5. **Power Supply**
   - **Official Raspberry Pi 4 Power Supply (5V 3A)**
   - **Alternative:** Quality USB-C power supply with sufficient amperage

6. **Network Connection**
   - **Ethernet (recommended):** For stable internet connection
   - **WiFi:** Built-in WiFi acceptable for most use cases

### Optional Components

1. **Case with Cooling**
   - Prevents overheating during continuous operation
   - Recommended for 24/7 operation

2. **External Storage**
   - USB 3.0 drive for storing generated images
   - Reduces wear on SD card

3. **Audio Interface (Advanced)**
   - Professional USB audio interface for better audio quality
   - Multiple microphone inputs for room coverage

## Physical Setup Instructions

### 1. Raspberry Pi Assembly

1. **Install Raspberry Pi OS:**
   ```bash
   # Use Raspberry Pi Imager to flash OS to SD card
   # Enable SSH and set username/password during imaging
   ```

2. **Insert SD Card:**
   - Insert the flashed SD card into the Raspberry Pi
   - Ensure it's fully seated

3. **Connect Peripherals:**
   - Connect HDMI cable to monitor
   - Connect USB microphone to any USB port
   - Connect Ethernet cable (if using wired connection)
   - Connect power supply last

### 2. Audio Hardware Setup

#### USB Microphone Configuration

1. **Connect Microphone:**
   - Use a high-quality USB cable
   - Connect directly to Raspberry Pi (avoid USB hubs if possible)
   - Ensure microphone is positioned for optimal room coverage

2. **Microphone Placement:**
   - **Distance:** 3-6 feet from typical conversation area
   - **Height:** Table level or slightly elevated
   - **Orientation:** Point toward conversation area
   - **Avoid:** Direct sunlight, air vents, noisy electronics

3. **Test Audio Input:**
   ```bash
   # List audio devices
   arecord -l
   
   # Test recording
   arecord -d 5 -f cd test.wav
   aplay test.wav
   ```

#### Audio Quality Optimization

1. **Room Acoustics:**
   - Minimize echo with soft furnishings
   - Avoid hard surfaces near microphone
   - Consider background noise levels

2. **Microphone Settings:**
   - Adjust gain levels if microphone supports it
   - Enable noise cancellation features
   - Test different positions for optimal pickup

### 3. Display Hardware Setup

#### HDMI Configuration

1. **Connect Display:**
   - Use high-quality HDMI cable
   - Connect to HDMI 0 port on Raspberry Pi
   - Ensure display is set to correct HDMI input

2. **Display Settings:**
   ```bash
   # Edit boot config
   sudo nano /boot/config.txt
   
   # Add/modify these lines:
   hdmi_force_hotplug=1
   hdmi_group=1
   hdmi_mode=16  # 1080p 60Hz
   hdmi_drive=2  # Force HDMI mode
   ```

3. **Test Display:**
   ```bash
   # Test framebuffer display
   sudo fbi -T 1 /opt/vc/src/hello_pi/hello_triangle/Mandelbrot.jpg
   ```

#### Display Optimization

1. **GPU Memory Split:**
   ```bash
   sudo raspi-config
   # Advanced Options > Memory Split > 128 or 256
   ```

2. **Overscan Settings:**
   ```bash
   # In /boot/config.txt
   disable_overscan=1
   ```

### 4. Network Setup

#### Ethernet Connection (Recommended)

1. **Connect Cable:**
   - Use Cat5e or better Ethernet cable
   - Connect to router/switch with internet access
   - Verify link LED indicators

2. **Test Connection:**
   ```bash
   ping google.com
   curl -I https://api.openai.com
   ```

#### WiFi Configuration

1. **Configure WiFi:**
   ```bash
   sudo raspi-config
   # System Options > Wireless LAN
   ```

2. **Optimize WiFi:**
   ```bash
   # Disable power management
   sudo iwconfig wlan0 power off
   ```

### 5. Power and Cooling

#### Power Supply

1. **Use Official Supply:**
   - Raspberry Pi 4 official power supply (5V 3A)
   - Avoid cheap/generic power supplies
   - Check for power warnings: `vcgencmd get_throttled`

2. **Power Management:**
   ```bash
   # Check power status
   vcgencmd measure_volts
   vcgencmd measure_temp
   ```

#### Cooling Solutions

1. **Passive Cooling:**
   - Heat sinks on CPU and RAM
   - Well-ventilated case
   - Avoid enclosed spaces

2. **Active Cooling:**
   - Small fan for continuous operation
   - Temperature-controlled fan scripts

3. **Monitor Temperature:**
   ```bash
   # Check CPU temperature
   vcgencmd measure_temp
   
   # Continuous monitoring
   watch -n 1 vcgencmd measure_temp
   ```

## Hardware Troubleshooting

### Audio Issues

#### No Audio Input Detected

**Symptoms:**
- Microphone not listed in `arecord -l`
- No audio levels in tests

**Solutions:**
1. **Check USB Connection:**
   ```bash
   lsusb | grep -i audio
   dmesg | grep -i audio
   ```

2. **Restart Audio Services:**
   ```bash
   sudo systemctl restart alsa-state
   pulseaudio --kill && pulseaudio --start
   ```

3. **Check Permissions:**
   ```bash
   sudo usermod -a -G audio $USER
   # Log out and back in
   ```

#### Poor Audio Quality

**Symptoms:**
- Low volume levels
- Background noise
- Distorted audio

**Solutions:**
1. **Adjust Microphone Position:**
   - Move closer to conversation area
   - Avoid reflective surfaces
   - Check for interference sources

2. **Audio Settings:**
   ```bash
   alsamixer  # Adjust input levels
   ```

3. **Test Different USB Ports:**
   - Try different USB ports
   - Avoid USB hubs
   - Check power supply adequacy

### Display Issues

#### No HDMI Output

**Symptoms:**
- Blank screen
- No signal detected

**Solutions:**
1. **Check Connections:**
   - Verify HDMI cable integrity
   - Try different HDMI port on display
   - Test with different display

2. **Force HDMI Output:**
   ```bash
   # In /boot/config.txt
   hdmi_force_hotplug=1
   hdmi_safe=1
   ```

3. **Check Boot Messages:**
   ```bash
   dmesg | grep -i hdmi
   ```

#### Display Resolution Issues

**Symptoms:**
- Incorrect resolution
- Overscan problems
- Aspect ratio issues

**Solutions:**
1. **Manual Resolution Setting:**
   ```bash
   # In /boot/config.txt
   hdmi_group=2
   hdmi_mode=82  # 1920x1080 60Hz
   ```

2. **Disable Overscan:**
   ```bash
   disable_overscan=1
   ```

### Performance Issues

#### High CPU Usage

**Symptoms:**
- System sluggish
- High temperature
- Throttling warnings

**Solutions:**
1. **Check Running Processes:**
   ```bash
   htop
   ps aux --sort=-%cpu
   ```

2. **Optimize Settings:**
   ```bash
   # Disable unnecessary services
   sudo systemctl disable bluetooth
   sudo systemctl disable wifi-powersave
   ```

3. **Improve Cooling:**
   - Add heat sinks
   - Improve ventilation
   - Add cooling fan

#### Memory Issues

**Symptoms:**
- Out of memory errors
- System freezing
- Swap usage high

**Solutions:**
1. **Increase Swap:**
   ```bash
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile
   # Set CONF_SWAPSIZE=2048
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

2. **Monitor Memory:**
   ```bash
   free -h
   htop
   ```

### Network Issues

#### Intermittent Connectivity

**Symptoms:**
- API calls failing
- Network timeouts
- Slow response times

**Solutions:**
1. **Use Ethernet:**
   - Switch from WiFi to Ethernet
   - Check cable quality
   - Verify router settings

2. **WiFi Optimization:**
   ```bash
   # Check signal strength
   iwconfig wlan0
   
   # Disable power management
   sudo iwconfig wlan0 power off
   ```

3. **Network Testing:**
   ```bash
   ping -c 10 8.8.8.8
   speedtest-cli
   ```

## Maintenance

### Regular Checks

1. **Weekly:**
   - Check system temperature
   - Verify audio input levels
   - Test display output

2. **Monthly:**
   - Clean dust from case/fans
   - Check SD card health
   - Update system packages

3. **Quarterly:**
   - Full system backup
   - Hardware connection inspection
   - Performance benchmarking

### Monitoring Scripts

Create monitoring scripts for automated health checks:

```bash
#!/bin/bash
# System health check script

echo "=== Voxel Hardware Health Check ==="
echo "Temperature: $(vcgencmd measure_temp)"
echo "Voltage: $(vcgencmd measure_volts)"
echo "Throttling: $(vcgencmd get_throttled)"
echo "Memory: $(free -h | grep Mem)"
echo "Disk: $(df -h / | tail -1)"
echo "Audio devices: $(arecord -l | grep card)"
```

## Safety Considerations

1. **Electrical Safety:**
   - Use proper power supplies
   - Avoid water near electronics
   - Ensure proper grounding

2. **Heat Management:**
   - Monitor temperatures regularly
   - Ensure adequate ventilation
   - Use thermal protection

3. **Data Protection:**
   - Regular backups
   - Surge protection
   - UPS for power stability

## Performance Optimization

### Hardware Upgrades

1. **Storage:**
   - USB 3.0 SSD for better I/O
   - High-speed SD card (A2 rating)

2. **Cooling:**
   - Active cooling solutions
   - Thermal interface materials

3. **Audio:**
   - Professional USB audio interface
   - Multiple microphone setup

### Configuration Tuning

1. **GPU Memory:**
   ```bash
   # Allocate more memory to GPU
   gpu_mem=256
   ```

2. **CPU Governor:**
   ```bash
   # Set performance governor
   echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   ```

This hardware setup guide ensures optimal performance and reliability for your Voxel ambient art generator installation.