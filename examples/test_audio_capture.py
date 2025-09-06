#!/usr/bin/env python3
"""
Example script to test audio capture functionality.
This script demonstrates how to use the AudioCapture class.
"""

import sys
import time
import logging
from pathlib import Path

# Add parent directory to path to import voxel modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from voxel.audio.capture import AudioCapture, AudioCaptureError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Test audio capture functionality."""
    print("Voxel Audio Capture Test")
    print("=" * 30)
    
    audio_capture = AudioCapture()
    
    try:
        print("Starting audio capture...")
        audio_capture.start_recording()
        
        print(f"Recording started successfully!")
        print(f"Sample rate: {audio_capture.sample_rate} Hz")
        print(f"Chunk duration: {audio_capture.chunk_duration} seconds")
        print(f"Channels: {audio_capture.channels}")
        print()
        
        print("Listening for audio chunks... (Press Ctrl+C to stop)")
        
        chunk_count = 0
        start_time = time.time()
        
        while True:
            # Get audio chunk with timeout
            chunk = audio_capture.get_audio_chunk(timeout=2.0)
            
            if chunk:
                chunk_count += 1
                data_size_kb = len(chunk.data) / 1024
                
                print(f"Chunk {chunk_count}:")
                print(f"  Timestamp: {chunk.timestamp.strftime('%H:%M:%S.%f')[:-3]}")
                print(f"  Duration: {chunk.duration:.1f}s")
                print(f"  Data size: {data_size_kb:.1f} KB")
                print(f"  Sample rate: {chunk.sample_rate} Hz")
                print(f"  Queue size: {audio_capture.get_queue_size()}")
                print()
                
                # Stop after 5 chunks for demo
                if chunk_count >= 5:
                    print("Demo complete - captured 5 audio chunks")
                    break
            else:
                print("No audio chunk received (timeout)")
                
            # Check if still recording
            if not audio_capture.is_recording():
                print("Recording stopped unexpectedly")
                break
                
    except AudioCaptureError as e:
        print(f"Audio capture error: {e}")
        return 1
        
    except KeyboardInterrupt:
        print("\nStopping audio capture...")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
        
    finally:
        # Clean shutdown
        if audio_capture.is_recording():
            audio_capture.stop_recording()
            
        elapsed_time = time.time() - start_time
        print(f"\nSession summary:")
        print(f"  Total chunks captured: {chunk_count}")
        print(f"  Total time: {elapsed_time:.1f} seconds")
        print(f"  Average chunks per second: {chunk_count / elapsed_time:.2f}")
        
    print("Audio capture test completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())