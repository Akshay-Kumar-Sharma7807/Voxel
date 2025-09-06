"""
Example script demonstrating SpeechProcessor functionality.
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import voxel
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from voxel.speech import SpeechProcessor
from voxel.models import AudioChunk


def main():
    """Demonstrate SpeechProcessor functionality."""
    print("Voxel Speech Processor Example")
    print("=" * 40)
    
    # Initialize the speech processor
    processor = SpeechProcessor()
    
    # Try to initialize the model
    print("Initializing Vosk model...")
    if processor.initialize_model():
        print("✓ Model initialized successfully")
    else:
        print("✗ Model initialization failed")
        print("Note: This is expected if you haven't downloaded the Vosk model yet.")
        print("To download the model, run:")
        print("  python -c \"import vosk; vosk.Model.download('vosk-model-small-en-us-0.15')\"")
        return
    
    # Create a mock audio chunk for testing
    # In a real application, this would come from the AudioCapture module
    mock_audio_data = b'\x00\x01' * 8000  # Mock 1 second of 16kHz audio
    audio_chunk = AudioChunk(
        data=mock_audio_data,
        timestamp=datetime.now(),
        duration=1.0,
        sample_rate=16000
    )
    
    print("\nTesting transcription with mock audio data...")
    result = processor.transcribe_audio(audio_chunk)
    
    print(f"Transcription result:")
    print(f"  Text: '{result.text}'")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Is valid: {result.is_valid}")
    print(f"  Timestamp: {result.timestamp}")
    
    # Test speech validation with different inputs
    print("\nTesting speech validation:")
    test_cases = [
        ("hello world", 0.8),
        ("", 0.8),
        ("hello", 0.8),
        ("uh um", 0.8),
        ("this is a test", 0.3),
        ("good morning everyone", 0.7)
    ]
    
    for text, confidence in test_cases:
        is_valid = processor.is_speech_detected(text, confidence)
        status = "✓" if is_valid else "✗"
        print(f"  {status} '{text}' (conf: {confidence}) -> {is_valid}")
    
    # Clean up
    processor.cleanup()
    print("\n✓ Speech processor cleaned up")
    print("Example completed successfully!")


if __name__ == "__main__":
    main()