"""
Audio capture functionality for continuous microphone recording.
"""

import time
import threading
from queue import Queue, Empty
from typing import Optional
from datetime import datetime

import sounddevice as sd
import numpy as np

from ..config import AudioConfig, ErrorConfig
from ..models import AudioChunk
from ..error_handler import ErrorCategory, ErrorSeverity, log_system_event
from ..exceptions import (
    AudioCaptureError, MicrophoneNotFoundError, 
    AudioPermissionError, AudioBufferOverflowError
)
from ..decorators import handle_errors, log_operation, retry_on_error


class AudioCapture:
    """
    Manages continuous audio recording from USB microphone with 5-second chunk buffering.
    
    Features:
    - Continuous recording in background thread
    - 5-second audio chunk buffering with queue management
    - Microphone detection and connection retry logic
    - Graceful error handling and recovery
    """
    
    def __init__(self, memory_manager=None):
        self.sample_rate = AudioConfig.SAMPLE_RATE
        self.chunk_duration = AudioConfig.CHUNK_DURATION
        self.channels = AudioConfig.CHANNELS
        self.buffer_size = AudioConfig.BUFFER_SIZE
        self.retry_interval = AudioConfig.RETRY_INTERVAL
        
        # Calculate samples per chunk
        self.samples_per_chunk = int(self.sample_rate * self.chunk_duration)
        
        # Audio stream and threading
        self._stream: Optional[sd.InputStream] = None
        self._recording_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Audio buffer management
        self._audio_queue: Queue[AudioChunk] = Queue(maxsize=10)  # Buffer up to 10 chunks
        self._current_buffer = np.array([], dtype=np.float32)
        
        # Memory management
        self._memory_manager = memory_manager
        self._chunk_counter = 0
        
        # Error tracking
        self._consecutive_errors = 0
        self._last_error_time = 0
        
        # Device management
        self._current_device = None
        
    @handle_errors(
        category=ErrorCategory.AUDIO_CAPTURE,
        severity=ErrorSeverity.HIGH,
        raise_on_critical=True
    )
    @log_operation(level="INFO")
    def start_recording(self) -> None:
        """
        Initialize audio stream and start continuous recording.
        
        Raises:
            AudioCaptureError: If microphone initialization fails
        """
        log_system_event("Starting audio capture...")
        
        # Detect and select microphone
        self._detect_microphone()
        
        # Initialize audio stream
        self._initialize_stream()
        
        # Start recording thread
        self._start_recording_thread()
        
        log_system_event(f"Audio capture started successfully with device: {self._current_device}")
    
    @handle_errors(
        category=ErrorCategory.AUDIO_CAPTURE,
        severity=ErrorSeverity.MEDIUM
    )
    @log_operation(level="INFO")
    def stop_recording(self) -> None:
        """Clean shutdown of audio resources."""
        log_system_event("Stopping audio capture...")
        
        # Signal stop to recording thread
        self._stop_event.set()
        
        # Wait for recording thread to finish
        if self._recording_thread and self._recording_thread.is_alive():
            self._recording_thread.join(timeout=5.0)
            
        # Close audio stream
        if self._stream:
            self._stream.close()
        self._stream = None
            
        # Clear any remaining audio chunks
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except Empty:
                break
                
        log_system_event("Audio capture stopped successfully")
    
    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[AudioChunk]:
        """
        Return next available 5-second audio buffer.
        
        Args:
            timeout: Maximum time to wait for audio chunk
            
        Returns:
            AudioChunk if available, None if timeout or no audio
        """
        try:
            return self._audio_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def is_recording(self) -> bool:
        """Check if audio capture is currently active."""
        return (self._stream is not None and 
                self._stream.active and 
                self._recording_thread is not None and 
                self._recording_thread.is_alive() and 
                not self._stop_event.is_set())
    
    def get_queue_size(self) -> int:
        """Get current number of audio chunks in queue."""
        return self._audio_queue.qsize()
    
    @retry_on_error(max_retries=3, delay=2.0)
    def _detect_microphone(self) -> None:
        """
        Detect available microphone devices and select the best one.
        
        Raises:
            MicrophoneNotFoundError: If no suitable microphone found
        """
        devices = sd.query_devices()
        
        # Look for USB microphones first, then any input device
        usb_devices = []
        microphone_devices = []
        input_devices = []
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                device_name = device['name'].lower()
                if 'usb' in device_name:
                    usb_devices.append((i, device))
                elif 'microphone' in device_name:
                    microphone_devices.append((i, device))
                else:
                    input_devices.append((i, device))
        
        # Prefer USB devices, then microphones, fallback to any input device
        if usb_devices:
            self._current_device = usb_devices[0][0]
            device_info = usb_devices[0][1]
        elif microphone_devices:
            self._current_device = microphone_devices[0][0]
            device_info = microphone_devices[0][1]
        elif input_devices:
            self._current_device = input_devices[0][0]
            device_info = input_devices[0][1]
        else:
            raise MicrophoneNotFoundError(
                "No input devices found",
                component="AudioCapture",
                additional_data={"available_devices": len(devices)}
            )
            
        log_system_event(f"Selected audio device: {device_info['name']} (ID: {self._current_device})")
    
    def _initialize_stream(self) -> None:
        """
        Initialize the audio input stream.
        
        Raises:
            AudioCaptureError: If stream initialization fails
            AudioPermissionError: If microphone permissions denied
        """
        try:
            self._stream = sd.InputStream(
                device=self._current_device,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                dtype=np.float32,
                callback=self._audio_callback
            )
            
            # Test the stream
            self._stream.start()
            time.sleep(0.1)  # Brief test
            
            if not self._stream.active:
                raise AudioCaptureError(
                    "Audio stream failed to start",
                    component="AudioCapture",
                    additional_data={"device_id": self._current_device}
                )
                
        except PermissionError as e:
            raise AudioPermissionError(
                "Microphone access denied - check permissions",
                component="AudioCapture",
                additional_data={"device_id": self._current_device}
            )
        except Exception as e:
            if "permission" in str(e).lower():
                raise AudioPermissionError(
                    f"Microphone permission error: {e}",
                    component="AudioCapture"
                )
            else:
                raise AudioCaptureError(
                    f"Audio stream initialization failed: {e}",
                    component="AudioCapture",
                    additional_data={"device_id": self._current_device}
                )
    
    def _start_recording_thread(self) -> None:
        """Start the background recording thread."""
        self._stop_event.clear()
        self._recording_thread = threading.Thread(
            target=self._recording_loop,
            name="AudioCaptureThread",
            daemon=True
        )
        self._recording_thread.start()
    
    def _recording_loop(self) -> None:
        """Main recording loop that runs in background thread."""
        logger.info("Audio recording loop started")
        
        while not self._stop_event.is_set():
            try:
                # Check if we have enough data for a chunk
                if len(self._current_buffer) >= self.samples_per_chunk:
                    self._process_audio_chunk()
                
                # Small sleep to prevent busy waiting
                time.sleep(0.01)
                
                # Reset error counter on successful operation
                self._consecutive_errors = 0
                
            except Exception as e:
                self._handle_recording_error(e)
                
        logger.info("Audio recording loop stopped")
    
    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        """
        Callback function for audio stream data.
        
        Args:
            indata: Input audio data
            frames: Number of frames
            time_info: Timing information
            status: Stream status
        """
        if status:
            logger.warning(f"Audio callback status: {status}")
            
        try:
            # Convert to mono if needed and append to buffer
            if indata.shape[1] > 1:
                audio_data = np.mean(indata, axis=1)
            else:
                audio_data = indata.flatten()
                
            self._current_buffer = np.concatenate([self._current_buffer, audio_data])
            
        except Exception as e:
            logger.error(f"Audio callback error: {e}")
    
    def _process_audio_chunk(self) -> None:
        """Process accumulated audio data into a chunk."""
        # Extract chunk data
        chunk_data = self._current_buffer[:self.samples_per_chunk]
        self._current_buffer = self._current_buffer[self.samples_per_chunk:]
        
        # Convert to bytes (16-bit PCM)
        audio_bytes = (chunk_data * 32767).astype(np.int16).tobytes()
        
        # Create AudioChunk
        audio_chunk = AudioChunk(
            data=audio_bytes,
            timestamp=datetime.now(),
            duration=self.chunk_duration,
            sample_rate=self.sample_rate
        )
        
        # Register with memory manager if available
        if self._memory_manager:
            chunk_id = f"chunk_{self._chunk_counter}"
            self._memory_manager.register_audio_buffer(chunk_id, audio_chunk)
            self._chunk_counter += 1
        
        # Add to queue (non-blocking)
        try:
            self._audio_queue.put_nowait(audio_chunk)
        except:
            # Queue is full, remove oldest chunk and add new one
            try:
                old_chunk = self._audio_queue.get_nowait()
                # Unregister old chunk from memory manager
                if self._memory_manager and hasattr(old_chunk, 'timestamp'):
                    old_chunk_id = f"chunk_{self._chunk_counter - self._audio_queue.maxsize - 1}"
                    self._memory_manager.unregister_buffer(old_chunk_id)
                
                self._audio_queue.put_nowait(audio_chunk)
                raise AudioBufferOverflowError(
                    "Audio queue overflow, dropped oldest chunk",
                    component="AudioCapture",
                    additional_data={"queue_size": self._audio_queue.qsize()}
                )
            except Empty:
                pass
    
    @handle_errors(
        category=ErrorCategory.AUDIO_CAPTURE,
        severity=ErrorSeverity.MEDIUM,
        return_on_error=None
    )
    def _handle_recording_error(self, error: Exception) -> None:
        """
        Handle errors during recording with retry logic.
        
        Args:
            error: The exception that occurred
        """
        self._consecutive_errors += 1
        current_time = time.time()
        
        log_system_event(
            f"Recording error ({self._consecutive_errors}): {error}",
            level="ERROR",
            consecutive_errors=self._consecutive_errors
        )
        
        # If too many consecutive errors, attempt recovery
        if self._consecutive_errors >= ErrorConfig.MAX_CONSECUTIVE_ERRORS:
            log_system_event("Too many consecutive errors, attempting recovery...", level="WARNING")
            
            try:
                # Wait before retry
                if current_time - self._last_error_time < self.retry_interval:
                    time.sleep(self.retry_interval - (current_time - self._last_error_time))
                
                # Attempt to reinitialize
                if self._stream:
                    self._stream.close()
                    
                self._detect_microphone()
                self._initialize_stream()
                
                log_system_event("Audio capture recovery successful")
                self._consecutive_errors = 0
                
            except Exception as recovery_error:
                log_system_event(
                    f"Audio capture recovery failed: {recovery_error}",
                    level="ERROR"
                )
                
                # If recovery fails, wait longer before next attempt
                time.sleep(self.retry_interval)
                
        self._last_error_time = current_time
        
        # Small delay before continuing
        time.sleep(ErrorConfig.ERROR_RECOVERY_DELAY)