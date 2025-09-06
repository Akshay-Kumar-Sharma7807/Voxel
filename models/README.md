# Vosk Models Directory

This directory contains the Vosk speech recognition models used by the Voxel ambient art generator.

## Required Model

The system requires the `vosk-model-small-en-us-0.15` model for on-device speech recognition.

### Download Instructions

To download the required model, run one of the following commands:

**Option 1: Using Python (Recommended)**
```bash
python -c "import vosk; vosk.Model.download('vosk-model-small-en-us-0.15')"
```

**Option 2: Manual Download**
1. Download from: https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
2. Extract the zip file
3. Place the extracted `vosk-model-small-en-us-0.15` folder in this directory

### Model Details

- **Name**: vosk-model-small-en-us-0.15
- **Size**: ~91 MB
- **Language**: English (US)
- **Type**: Small model optimized for Raspberry Pi
- **Accuracy**: Good for conversational speech
- **Performance**: Optimized for real-time processing

### Directory Structure

After downloading, your models directory should look like:
```
models/
├── README.md
└── vosk-model-small-en-us-0.15/
    ├── am/
    ├── graph/
    ├── ivector/
    ├── conf/
    └── README
```

### Privacy Note

This model runs entirely on-device, ensuring that no audio data is transmitted over the network during speech recognition. Only the processed text results are used for subsequent image generation API calls.