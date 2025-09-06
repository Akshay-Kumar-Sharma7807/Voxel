"""
Unit tests for audio capture functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import threading
import time
import numpy as np
from queue import Empty
from datetime import datetime

from voxel.audio.capture import AudioCapture, AudioCaptureError
from voxel.models import AudioChunk


class TestAudioCapture(unittest.TestCase):
    """Test cases for AudioCapture class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_capture = AudioCapture()
    
    def tearDown(self):
        """Clean up after tests."""
        if self.audio_capture.is_recording():
            self.audio_capture.stop_recording()
    
    @patch('voxel.audio.capture.sd.query_devices')
    def test_detect_microphone_usb_device(self, mock_query_devices):
        """Test microphone detection with USB device available."""
        # Mock device list with USB microphone
        mock_devices = [
            {'name': 'Built-in Microphone', 'max_input_channels': 1},
            {'name': 'USB Microphone', 'max_input_channels': 1},
            {'name': 'Speakers', 'max_input_channels': 0}
        ]
        mock_query_devices.return_value = mock_devices
        
        self.audio_capture._detect_microphone()
        
        # Should select USB microphone (index 1)
        self.assertEqual(self.audio_capture._current_device, 1)
    
    @patch('voxel.audio.capture.sd.query_devices')
    def test_detect_microphone_fallback_device(self, mock_query_devices):
        """Test microphone detection fallback to any input device."""
        # Mock device list without USB microphone
        mock_devices = [
            {'name': 'Built-in Microphone', 'max_input_channels': 1},
            {'name': 'Speakers', 'max_input_channels': 0}
        ]
        mock_query_devices.return_value = mock_devices
        
        self.audio_capture._detect_microphone()
        
        # Should select built-in microphone (index 0)
        self.assertEqual(self.audio_capture._current_device, 0)
    
    @patch('voxel.audio.capture.sd.query_devices')
    def test_detect_microphone_no_devices(self, mock_query_devices):
        """Test microphone detection with no input devices."""
        # Mock device list with no input devices
        mock_devices = [
            {'name': 'Speakers', 'max_input_channels': 0}
        ]
        mock_query_devices.return_value = mock_devices
        
        with self.assertRaises(AudioCaptureError):
            self.audio_capture._detect_microphone()
    
    @patch('voxel.audio.capture.sd.InputStream')
    @patch('voxel.audio.capture.sd.query_devices')
    def test_initialize_stream_success(self, mock_query_devices, mock_input_stream):
        """Test successful audio stream initialization."""
        # Mock device detection
        mock_devices = [{'name': 'Test Mic', 'max_input_channels': 1}]
        mock_query_devices.return_value = mock_devices
        
        # Mock stream
        mock_stream = Mock()
        mock_stream.active = True
        mock_input_stream.return_value = mock_stream
        
        self.audio_capture._detect_microphone()
        self.audio_capture._initialize_stream()
        
        # Verify stream was created and started
        mock_input_stream.assert_called_once()
        mock_stream.start.assert_called_once()
        self.assertEqual(self.audio_capture._stream, mock_stream)
    
    @patch('voxel.audio.capture.sd.InputStream')
    @patch('voxel.audio.capture.sd.query_devices')
    def test_initialize_stream_failure(self, mock_query_devices, mock_input_stream):
        """Test audio stream initialization failure."""
        # Mock device detection
        mock_devices = [{'name': 'Test Mic', 'max_input_channels': 1}]
        mock_query_devices.return_value = mock_devices
        
        # Mock stream that fails to start
        mock_stream = Mock()
        mock_stream.active = False
        mock_input_stream.return_value = mock_stream
        
        self.audio_capture._detect_microphone()
        
        with self.assertRaises(AudioCaptureError):
            self.audio_capture._initialize_stream()
    
    @patch('voxel.audio.capture.sd.InputStream')
    @patch('voxel.audio.capture.sd.query_devices')
    def test_start_recording_success(self, mock_query_devices, mock_input_stream):
        """Test successful recording start."""
        # Mock device detection
        mock_devices = [{'name': 'Test Mic', 'max_input_channels': 1}]
        mock_query_devices.return_value = mock_devices
        
        # Mock stream
        mock_stream = Mock()
        mock_stream.active = True
        mock_input_stream.return_value = mock_stream
        
        self.audio_capture.start_recording()
        
        # Verify recording is active
        self.assertTrue(self.audio_capture.is_recording())
        self.assertIsNotNone(self.audio_capture._recording_thread)
        self.assertTrue(self.audio_capture._recording_thread.is_alive())
    
    def test_stop_recording(self):
        """Test recording stop functionality."""
        # Mock a running recording session
        self.audio_capture._stop_event = threading.Event()
        self.audio_capture._recording_thread = Mock()
        self.audio_capture._recording_thread.is_alive.return_value = True
        mock_stream = Mock()
        self.audio_capture._stream = mock_stream
        
        self.audio_capture.stop_recording()
        
        # Verify stop event was set and stream was closed
        self.assertTrue(self.audio_capture._stop_event.is_set())
        self.audio_capture._recording_thread.join.assert_called_once()
        mock_stream.close.assert_called_once()
        self.assertIsNone(self.audio_capture._stream)
    
    def test_audio_callback_mono(self):
        """Test audio callback with mono input."""
        # Create mock mono audio data
        frames = 1024
        indata = np.random.random((frames, 1)).astype(np.float32)
        
        initial_buffer_size = len(self.audio_capture._current_buffer)
        
        self.audio_capture._audio_callback(indata, frames, None, None)
        
        # Verify buffer was updated
        expected_size = initial_buffer_size + frames
        self.assertEqual(len(self.audio_capture._current_buffer), expected_size)
    
    def test_audio_callback_stereo(self):
        """Test audio callback with stereo input (should convert to mono)."""
        # Create mock stereo audio data
        frames = 1024
        indata = np.random.random((frames, 2)).astype(np.float32)
        
        initial_buffer_size = len(self.audio_capture._current_buffer)
        
        self.audio_capture._audio_callback(indata, frames, None, None)
        
        # Verify buffer was updated with mono data
        expected_size = initial_buffer_size + frames
        self.assertEqual(len(self.audio_capture._current_buffer), expected_size)
    
    def test_process_audio_chunk(self):
        """Test audio chunk processing."""
        # Fill buffer with enough data for one chunk
        samples_needed = self.audio_capture.samples_per_chunk
        test_data = np.random.random(samples_needed).astype(np.float32)
        self.audio_capture._current_buffer = test_data.copy()
        
        self.audio_capture._process_audio_chunk()
        
        # Verify chunk was created and added to queue
        self.assertEqual(self.audio_capture.get_queue_size(), 1)
        
        # Verify buffer was reduced
        self.assertEqual(len(self.audio_capture._current_buffer), 0)
        
        # Verify chunk properties
        chunk = self.audio_capture.get_audio_chunk()
        self.assertIsInstance(chunk, AudioChunk)
        self.assertEqual(chunk.duration, self.audio_capture.chunk_duration)
        self.assertEqual(chunk.sample_rate, self.audio_capture.sample_rate)
        self.assertIsInstance(chunk.timestamp, datetime)
    
    def test_get_audio_chunk_timeout(self):
        """Test get_audio_chunk with timeout when no data available."""
        # Queue should be empty
        chunk = self.audio_capture.get_audio_chunk(timeout=0.1)
        self.assertIsNone(chunk)
    
    def test_get_audio_chunk_success(self):
        """Test successful audio chunk retrieval."""
        # Add a test chunk to queue
        test_chunk = AudioChunk(
            data=b'test_data',
            timestamp=datetime.now(),
            duration=5.0,
            sample_rate=16000
        )
        self.audio_capture._audio_queue.put(test_chunk)
        
        chunk = self.audio_capture.get_audio_chunk()
        self.assertEqual(chunk, test_chunk)
    
    def test_queue_overflow_handling(self):
        """Test queue overflow handling (should drop oldest chunk)."""
        # Fill queue to capacity
        queue_capacity = 10
        for i in range(queue_capacity + 2):  # Exceed capacity
            samples_needed = self.audio_capture.samples_per_chunk
            test_data = np.random.random(samples_needed).astype(np.float32)
            self.audio_capture._current_buffer = test_data.copy()
            self.audio_capture._process_audio_chunk()
        
        # Queue should not exceed capacity
        self.assertLessEqual(self.audio_capture.get_queue_size(), queue_capacity)
    
    def test_is_recording_false_initially(self):
        """Test is_recording returns False initially."""
        self.assertFalse(self.audio_capture.is_recording())
    
    def test_get_queue_size_initially_zero(self):
        """Test queue size is initially zero."""
        self.assertEqual(self.audio_capture.get_queue_size(), 0)
    
    @patch('voxel.audio.capture.sd.query_devices')
    def test_handle_recording_error_recovery(self, mock_query_devices):
        """Test error handling and recovery logic."""
        # Mock device detection for recovery
        mock_devices = [{'name': 'Test Mic', 'max_input_channels': 1}]
        mock_query_devices.return_value = mock_devices
        
        # Simulate multiple errors
        test_error = Exception("Test error")
        
        # Should not raise exception, should attempt recovery
        for i in range(3):
            self.audio_capture._handle_recording_error(test_error)
        
        # Error count should be tracked
        self.assertEqual(self.audio_capture._consecutive_errors, 3)
    
    def test_audio_chunk_data_format(self):
        """Test that audio chunk data is properly formatted as 16-bit PCM."""
        # Create test audio data
        samples_needed = self.audio_capture.samples_per_chunk
        test_data = np.random.uniform(-1, 1, samples_needed).astype(np.float32)
        self.audio_capture._current_buffer = test_data.copy()
        
        self.audio_capture._process_audio_chunk()
        
        chunk = self.audio_capture.get_audio_chunk()
        
        # Verify data is bytes
        self.assertIsInstance(chunk.data, bytes)
        
        # Verify data length (16-bit = 2 bytes per sample)
        expected_bytes = samples_needed * 2
        self.assertEqual(len(chunk.data), expected_bytes)


class TestAudioCaptureIntegration(unittest.TestCase):
    """Integration tests for AudioCapture with mocked sounddevice."""
    
    @patch('voxel.audio.capture.sd.InputStream')
    @patch('voxel.audio.capture.sd.query_devices')
    def test_full_recording_cycle(self, mock_query_devices, mock_input_stream):
        """Test complete recording cycle with mock audio input."""
        # Mock device detection
        mock_devices = [{'name': 'Test Mic', 'max_input_channels': 1}]
        mock_query_devices.return_value = mock_devices
        
        # Mock stream
        mock_stream = Mock()
        mock_stream.active = True
        mock_input_stream.return_value = mock_stream
        
        audio_capture = AudioCapture()
        
        try:
            # Start recording
            audio_capture.start_recording()
            self.assertTrue(audio_capture.is_recording())
            
            # Simulate audio callback with enough data for one chunk
            samples_per_chunk = audio_capture.samples_per_chunk
            test_audio = np.random.random((samples_per_chunk, 1)).astype(np.float32)
            
            # Call audio callback multiple times to build up a chunk
            chunk_size = 1024
            for i in range(0, samples_per_chunk, chunk_size):
                end_idx = min(i + chunk_size, samples_per_chunk)
                audio_slice = test_audio[i:end_idx]
                audio_capture._audio_callback(audio_slice, len(audio_slice), None, None)
            
            # Wait a bit for processing
            time.sleep(0.1)
            
            # Should have at least one chunk available
            chunk = audio_capture.get_audio_chunk(timeout=1.0)
            self.assertIsNotNone(chunk)
            self.assertIsInstance(chunk, AudioChunk)
            
        finally:
            audio_capture.stop_recording()
            self.assertFalse(audio_capture.is_recording())


if __name__ == '__main__':
    unittest.main()