# Models Directory

This directory contains the machine learning models used by the Voxel ambient art generator for on-device speech recognition.

## Overview

Voxel uses Vosk speech recognition models to process audio locally, ensuring complete privacy by never sending audio data over the network. Only processed text is used for image generation API calls.

## Vosk Speech Recognition Models

### Supported Models

#### 1. Small English Model (Recommended)
- **File**: vosk-model-small-en-us-0.15
- **Size**: ~91MB download, ~150MB extracted
- **Memory Usage**: ~200MB during operation
- **Accuracy**: Good for conversational speech
- **Best For**: Raspberry Pi 4 (4GB+), general use cases
- **Download URL**: https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip

#### 2. Large English Model (Advanced)
- **File**: vosk-model-en-us-0.22
- **Size**: ~1.8GB download, ~2.2GB extracted
- **Memory Usage**: ~500MB during operation
- **Accuracy**: Excellent for all speech types
- **Best For**: Raspberry Pi 4 (8GB), high-accuracy requirements
- **Download URL**: https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip

### Required Directory Structure

After installation, your models directory should look like this:

```
models/
└── vosk-model-en/          # Renamed from downloaded model
    ├── am/
    │   ├── final.mdl       # Acoustic model
    │   └── ...
    ├── conf/
    │   ├── mfcc.conf       # Feature extraction config
    │   ├── model.conf      # Model configuration
    │   └── ...
    ├── graph/
    │   ├── HCLG.fst        # Decoding graph
    │   ├── words.txt       # Vocabulary
    │   └── ...
    ├── ivector/            # Optional: speaker adaptation
    └── rescore/            # Optional: language model rescoring
```

## Installation Methods

### Method 1: Automated Setup (Recommended)

Use the provided setup script:

```bash
# Run the setup script
./scripts/setup_vosk_model.sh
```

The script will:
- Check system requirements
- Download the appropriate model
- Verify model integrity
- Test model loading
- Provide troubleshooting information

### Method 2: Manual Installation

#### For Small Model (Recommended):

```bash
# Navigate to models directory
cd models

# Download the model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip

# Extract the model
unzip vosk-model-small-en-us-0.15.zip

# Rename to expected directory name
mv vosk-model-small-en-us-0.15 vosk-model-en

# Clean up
rm vosk-model-small-en-us-0.15.zip

# Return to project root
cd ..
```

#### For Large Model (Advanced):

```bash
# Navigate to models directory
cd models

# Download the large model (1.8GB)
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip

# Extract the model
unzip vosk-model-en-us-0.22.zip

# Rename to expected directory name
mv vosk-model-en-us-0.22 vosk-model-en

# Clean up
rm vosk-model-en-us-0.22.zip

# Return to project root
cd ..
```

## Model Verification

### Test Model Loading

Test that the model loads correctly in Python:

```bash
# Activate virtual environment
source venv/bin/activate

# Test model loading
python3 -c "
import vosk
import json
import os

model_path = 'models/vosk-model-en'
if os.path.exists(model_path):
    try:
        model = vosk.Model(model_path)
        print('✓ Model loaded successfully')
        
        # Test recognizer
        rec = vosk.KaldiRecognizer(model, 16000)
        print('✓ Recognizer created successfully')
        
        # Test with dummy data
        dummy_audio = b'\x00' * 3200  # 0.2s of silence
        rec.AcceptWaveform(dummy_audio)
        result = rec.Result()
        print('✓ Recognition test completed')
        print('Model test: PASSED')
    except Exception as e:
        print('✗ Model test failed:', e)
else:
    print('✗ Model not found at:', model_path)
"
```

## Troubleshooting

### Common Issues

#### Model Not Found Error
```
FileNotFoundError: [Errno 2] No such file or directory: 'models/vosk-model-en'
```

**Solutions:**
1. Verify model directory exists: `ls -la models/`
2. Check directory name is exactly `vosk-model-en`
3. Re-run installation script: `./scripts/setup_vosk_model.sh`
4. Check file permissions: `chmod -R 755 models/vosk-model-en`

#### Model Loading Error
```
RuntimeError: Model loading failed
```

**Solutions:**
1. Verify model file integrity
2. Check available memory: `free -h`
3. Try smaller model if using large model
4. Re-download model (may be corrupted)

#### Memory Issues
```
MemoryError: Unable to allocate memory for model
```

**Solutions:**
1. Use smaller model (vosk-model-small-en-us-0.15)
2. Increase swap space
3. Close other applications
4. Restart system to free memory

### Performance Benchmarks

#### Expected Performance (Raspberry Pi 4):

**Small Model:**
- Loading time: 5-10 seconds
- Recognition latency: 1-3 seconds per 5-second chunk
- Memory usage: 200-300MB
- CPU usage: 30-50% during recognition

**Large Model:**
- Loading time: 15-30 seconds
- Recognition latency: 2-5 seconds per 5-second chunk
- Memory usage: 500-700MB
- CPU usage: 50-80% during recognition

## Privacy Note

This model runs entirely on-device, ensuring that no audio data is transmitted over the network during speech recognition. Only the processed text results are used for subsequent image generation API calls, maintaining complete privacy for conversations.