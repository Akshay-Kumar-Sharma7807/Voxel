"""
Unit tests for the SpeechProcessor class.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
from pathlib import Path

from voxel.speech.processor import SpeechProcessor, ModelLoadError, TranscriptionError
from voxel.models import AudioChunk, TranscriptionResult
from voxel.config import SpeechConfig, AudioConfig


class TestSpeechProcessor(unittest.TestCase):
    """Test cases for SpeechProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = SpeechProcessor()
        self.sample_audio_chunk = AudioChunk(
            data=b'\x00\x01' * 1000,  # Mock audio data
            timestamp=datetime.now(),
            duration=5.0,
            sample_rate=16000
        )
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.processor, 'cleanup'):
            self.processor.cleanup()
    
    @patch('voxel.speech.processor.vosk.Model')
    @patch('voxel.speech.processor.vosk.KaldiRecognizer')
    @patch('voxel.speech.processor.Path.exists')
    def test_initialize_model_success(self, mock_exists, mock_recognizer, mock_model):
        """Test successful model initialization."""
        # Setup mocks
        mock_exists.return_value = True
        mock_model_instance = Mock()
        mock_recognizer_instance = Mock()
        mock_model.return_value = mock_model_instance
        mock_recognizer.return_value = mock_recognizer_instance
        
        # Test initialization
        result = self.processor.initialize_model()
        
        # Assertions
        self.assertTrue(result)
        self.assertTrue(self.processor.is_initialized)
        self.assertEqual(self.processor.model, mock_model_instance)
        self.assertEqual(self.processor.recognizer, mock_recognizer_instance)
        
        # Verify model was loaded with correct path
        mock_model.assert_called_once()
        mock_recognizer.assert_called_once_with(mock_model_instance, AudioConfig.SAMPLE_RATE)
    
    @patch('voxel.speech.processor.Path.exists')
    def test_initialize_model_missing_model(self, mock_exists):
        """Test initialization failure when model is missing."""
        mock_exists.return_value = False
        
        result = self.processor.initialize_model()
        
        self.assertFalse(result)
        self.assertFalse(self.processor.is_initialized)
        self.assertIsNone(self.processor.model)
        self.assertIsNone(self.processor.recognizer)
    
    @patch('voxel.speech.processor.vosk.Model')
    @patch('voxel.speech.processor.Path.exists')
    def test_initialize_model_exception(self, mock_exists, mock_model):
        """Test initialization failure due to exception."""
        mock_exists.return_value = True
        mock_model.side_effect = Exception("Model load failed")
        
        result = self.processor.initialize_model()
        
        self.assertFalse(result)
        self.assertFalse(self.processor.is_initialized)
    
    def test_transcribe_audio_not_initialized(self):
        """Test transcription when processor is not initialized."""
        result = self.processor.transcribe_audio(self.sample_audio_chunk)
        
        self.assertIsInstance(result, TranscriptionResult)
        self.assertEqual(result.text, "")
        self.assertEqual(result.confidence, 0.0)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.timestamp, self.sample_audio_chunk.timestamp)
    
    @patch('voxel.speech.processor.vosk.Model')
    @patch('voxel.speech.processor.vosk.KaldiRecognizer')
    @patch('voxel.speech.processor.Path.exists')
    def test_transcribe_audio_success(self, mock_exists, mock_recognizer, mock_model):
        """Test successful audio transcription."""
        # Setup mocks
        mock_exists.return_value = True
        mock_model_instance = Mock()
        mock_recognizer_instance = Mock()
        mock_model.return_value = mock_model_instance
        mock_recognizer.return_value = mock_recognizer_instance
        
        # Mock successful recognition
        mock_recognizer_instance.AcceptWaveform.return_value = True
        mock_recognizer_instance.Result.return_value = json.dumps({
            'text': 'hello world test',
            'result': [
                {'word': 'hello', 'conf': 0.9},
                {'word': 'world', 'conf': 0.8},
                {'word': 'test', 'conf': 0.85}
            ]
        })
        
        # Initialize and test
        self.processor.initialize_model()
        result = self.processor.transcribe_audio(self.sample_audio_chunk)
        
        # Assertions
        self.assertIsInstance(result, TranscriptionResult)
        self.assertEqual(result.text, 'hello world test')
        self.assertGreater(result.confidence, 0.8)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.timestamp, self.sample_audio_chunk.timestamp)
    
    @patch('voxel.speech.processor.vosk.Model')
    @patch('voxel.speech.processor.vosk.KaldiRecognizer')
    @patch('voxel.speech.processor.Path.exists')
    def test_transcribe_audio_partial_result(self, mock_exists, mock_recognizer, mock_model):
        """Test transcription with partial result."""
        # Setup mocks
        mock_exists.return_value = True
        mock_model_instance = Mock()
        mock_recognizer_instance = Mock()
        mock_model.return_value = mock_model_instance
        mock_recognizer.return_value = mock_recognizer_instance
        
        # Mock partial recognition
        mock_recognizer_instance.AcceptWaveform.return_value = False
        mock_recognizer_instance.PartialResult.return_value = json.dumps({
            'partial': 'hello world'
        })
        
        # Initialize and test
        self.processor.initialize_model()
        result = self.processor.transcribe_audio(self.sample_audio_chunk)
        
        # Assertions
        self.assertIsInstance(result, TranscriptionResult)
        # Partial results might have empty text field
        self.assertIsNotNone(result.text)
    
    def test_calculate_confidence_with_word_confidences(self):
        """Test confidence calculation with word-level confidences."""
        result = {
            'text': 'hello world',
            'result': [
                {'word': 'hello', 'conf': 0.9},
                {'word': 'world', 'conf': 0.7}
            ]
        }
        
        confidence = self.processor._calculate_confidence(result)
        self.assertAlmostEqual(confidence, 0.8, places=2)
    
    def test_calculate_confidence_without_word_confidences(self):
        """Test confidence calculation without word-level confidences."""
        result = {'text': 'hello world test'}
        
        confidence = self.processor._calculate_confidence(result)
        self.assertEqual(confidence, 0.8)  # 3+ words
        
        result = {'text': 'hello world'}
        confidence = self.processor._calculate_confidence(result)
        self.assertEqual(confidence, 0.6)  # 2 words
        
        result = {'text': 'hello'}
        confidence = self.processor._calculate_confidence(result)
        self.assertEqual(confidence, 0.4)  # 1 word
        
        result = {'text': ''}
        confidence = self.processor._calculate_confidence(result)
        self.assertEqual(confidence, 0.0)  # no words
    
    def test_is_speech_detected_valid_cases(self):
        """Test speech detection for valid cases."""
        # Valid speech with good confidence
        self.assertTrue(self.processor.is_speech_detected("hello world", 0.8))
        
        # Valid speech at threshold
        self.assertTrue(self.processor.is_speech_detected("good morning", 0.5))
        
        # Longer valid speech
        self.assertTrue(self.processor.is_speech_detected("this is a test sentence", 0.7))
    
    def test_is_speech_detected_invalid_cases(self):
        """Test speech detection for invalid cases."""
        # Low confidence
        self.assertFalse(self.processor.is_speech_detected("hello world", 0.3))
        
        # Empty text
        self.assertFalse(self.processor.is_speech_detected("", 0.8))
        self.assertFalse(self.processor.is_speech_detected("   ", 0.8))
        
        # Single word
        self.assertFalse(self.processor.is_speech_detected("hello", 0.8))
        
        # Only filler words
        self.assertFalse(self.processor.is_speech_detected("uh um", 0.8))
        self.assertFalse(self.processor.is_speech_detected("ah er hm", 0.8))
    
    def test_cleanup(self):
        """Test cleanup method."""
        # Set some mock objects
        self.processor.model = Mock()
        self.processor.recognizer = Mock()
        self.processor.is_initialized = True
        
        # Call cleanup
        self.processor.cleanup()
        
        # Verify cleanup
        self.assertIsNone(self.processor.model)
        self.assertIsNone(self.processor.recognizer)
        self.assertFalse(self.processor.is_initialized)
    
    def test_get_default_model_path(self):
        """Test default model path generation."""
        path = self.processor._get_default_model_path()
        self.assertIn(SpeechConfig.MODEL_NAME, path)
        self.assertTrue(Path(path).is_absolute() or str(Path(path)).startswith('models'))


class TestSpeechProcessorIntegration(unittest.TestCase):
    """Integration tests for SpeechProcessor with sample audio."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.processor = SpeechProcessor()
    
    def tearDown(self):
        """Clean up after integration tests."""
        if hasattr(self.processor, 'cleanup'):
            self.processor.cleanup()
    
    @unittest.skip("Requires actual Vosk model - enable for integration testing")
    def test_real_model_initialization(self):
        """Test with real Vosk model (requires model to be downloaded)."""
        result = self.processor.initialize_model()
        self.assertTrue(result, "Model initialization failed - ensure Vosk model is downloaded")
        self.assertTrue(self.processor.is_initialized)
    
    @unittest.skip("Requires actual audio files - enable for integration testing")
    def test_real_audio_transcription(self):
        """Test with real audio files (requires sample audio files)."""
        # This test would require actual audio files
        # Implementation would load sample WAV files and test transcription
        pass


if __name__ == '__main__':
    unittest.main()