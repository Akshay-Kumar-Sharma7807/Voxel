# Voxel Ambient Art Generator

An AI-powered ambient art generator that creates beautiful voxel-style images based on voice input. The system listens to your speech, analyzes the content for mood and themes, then generates corresponding ambient artwork.

## Features

- **Voice-Activated**: Speak naturally to generate art
- **Multiple AI Providers**: Support for Freepik, OpenAI DALL-E, and Google Cloud
- **Real-time Processing**: On-device speech recognition with Vosk
- **Ambient Display**: Fullscreen image display optimized for Raspberry Pi
- **Intelligent Analysis**: Advanced text analysis for mood and theme detection

## Quick Start

### 1. Install Dependencies
```bash
# Clone the repository
git clone <repository-url> voxel-art-generator
cd voxel-art-generator

# Install dependencies (Linux/Raspberry Pi)
./scripts/install_dependencies.sh

# Or manually install
pip install -r requirements.txt
```

### 2. Setup API Key (Freepik Recommended)
```bash
# Copy environment template
cp .env.example .env

# Edit and add your Freepik API key
nano .env
```

Add to `.env`:
```
FREEPIK_API_KEY=your-freepik-api-key-here
IMAGE_PROVIDER=freepik
```

### 3. Download Speech Model
```bash
./scripts/setup_vosk_model.sh
```

### 4. Run the Application
```bash
python voxel.py
```

## API Provider Setup

### Freepik AI (Recommended)
- **Cost**: Most affordable option (~$10-15/month)
- **Quality**: High-quality images with multiple styles
- **Setup**: See [FREEPIK_SETUP.md](FREEPIK_SETUP.md)

### OpenAI DALL-E 3
- **Cost**: Higher cost per image
- **Quality**: Excellent, industry-leading results
- **Setup**: Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)

### Google Cloud Vertex AI
- **Cost**: Pay-per-use pricing
- **Quality**: Good quality with Imagen models
- **Setup**: See [GOOGLE_CLOUD_SETUP.md](GOOGLE_CLOUD_SETUP.md)

## Hardware Requirements

### Minimum (Development)
- Any modern computer with microphone
- Python 3.8+ support
- Internet connection for API calls

### Recommended (Production)
- Raspberry Pi 4 (4GB+ RAM)
- USB microphone
- HDMI display
- Stable internet connection

See [HARDWARE_SETUP.md](HARDWARE_SETUP.md) for detailed requirements.

## Documentation

- **[Installation Guide](INSTALLATION.md)** - Complete setup instructions
- **[Freepik Setup](FREEPIK_SETUP.md)** - Freepik API configuration
- **[Hardware Setup](HARDWARE_SETUP.md)** - Hardware requirements and optimization
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions
- **[Google Cloud Setup](GOOGLE_CLOUD_SETUP.md)** - Google Cloud configuration

## Project Structure

```
voxel-art-generator/
├── voxel/                  # Main application code
│   ├── audio/             # Audio capture and processing
│   ├── speech/            # Speech recognition
│   ├── analysis/          # Text analysis and mood detection
│   ├── generation/        # Image generation
│   ├── display/           # Image display management
│   └── performance/       # Performance monitoring
├── examples/              # Example scripts and tests
├── tests/                 # Unit tests
├── models/                # Vosk speech recognition models
├── generated_images/      # Generated artwork storage
├── scripts/               # Installation and setup scripts
└── docs/                  # Additional documentation
```

## Usage Examples

### Basic Voice Input
1. Run the application: `python voxel.py`
2. Speak naturally: "I'm feeling peaceful, like a sunset over calm waters"
3. Watch as the system generates corresponding ambient art

### Testing Components
```bash
# Test audio capture
python examples/test_audio_capture.py

# Test speech recognition
python examples/test_speech_processor.py

# Test image generation
python examples/test_image_generator.py

# Test complete workflow
python examples/test_main_controller.py
```

## Configuration

Key configuration options in `voxel/config.py`:

```python
# Image generation provider
PROVIDER = "freepik"  # freepik, openai, google_cloud

# Freepik settings
FREEPIK_IMAGE_SIZE = "square_1_1"
FREEPIK_STYLE = "photo"
FREEPIK_LIGHTING = "warm"

# Audio settings
SAMPLE_RATE = 16000
CHUNK_DURATION = 5.0
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Documentation**: Check the guides in the docs/ directory
- **Issues**: Report bugs and request features via GitHub issues
- **Community**: Join discussions in the project forums

## Acknowledgments

- **Vosk**: On-device speech recognition
- **Freepik**: Affordable AI image generation
- **OpenAI**: DALL-E 3 image generation
- **Google Cloud**: Vertex AI and Imagen models