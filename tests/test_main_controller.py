"""
Integration tests for the MainController and complete end-to-end workflow.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from voxel.controller import MainController, MainControllerError, ComponentInitializationError
from voxel.models import AudioChunk, TranscriptionResult, AnalysisResult, ImagePrompt, GeneratedImage
from voxel.config import SystemConfig


class TestMainController:
    """Test suite for MainController functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.controller = MainController()
    
    def teardown_method(self):
        """Clean up after tests."""
        if self.controller.is_running:
            self.controller.shutdown()
    
    def test_initialization(self):
        """Test MainController initialization."""
        assert not self.controller.is_running
        assert not self.controller.shutdown_requested
        assert self.controller.cycle_count == 0
        assert self.controller.error_count == 0
        assert self.controller.consecutive_errors == 0
        assert self.controller.stats['cycles_completed'] == 0
        assert self.controller.stats['images_generated'] == 0
        assert self.controller.stats['errors_encountered'] == 0
    
    @patch('voxel.controller.AudioCapture')
    @patch('voxel.controller.SpeechProcessor')
    @patch('voxel.controller.TextAnalyzer')
    @patch('voxel.controller.PromptCrafter')
    @patch('voxel.controller.ImageGenerator')
    @patch('voxel.controller.DisplayController')
    def test_initialize_components_success(self, mock_display, mock_generator, mock_crafter, 
                                         mock_analyzer, mock_speech, mock_audio):
        """Test successful component initialization."""
        # Mock speech processor initialization
        mock_speech_instance = Mock()
        mock_speech_instance.initialize_model.return_value = True
        mock_speech.return_value = mock_speech_instance
        
        # Initialize components
        result = self.controller.initialize_components()
        
        assert result is True
        assert self.controller.audio_capture is not None
        assert self.controller.speech_processor is not None
        assert self.controller.text_analyzer is not None
        assert self.controller.prompt_crafter is not None
        assert self.controller.image_generator is not None
        assert self.controller.display_controller is not None
    
    @patch('voxel.controller.SpeechProcessor')
    def test_initialize_components_speech_failure(self, mock_speech):
        """Test component initialization with speech processor failure."""
        # Mock speech processor initialization failure
        mock_speech_instance = Mock()
        mock_speech_instance.initialize_model.return_value = False
        mock_speech.return_value = mock_speech_instance
        
        result = self.controller.initialize_components()
        
        assert result is False
    
    @patch('voxel.controller.AudioCapture')
    def test_initialize_components_exception(self, mock_audio):
        """Test component initialization with exception."""
        # Mock audio capture to raise exception
        mock_audio.side_effect = Exception("Audio initialization failed")
        
        result = self.controller.initialize_components()
        
        assert result is False
    
    def test_get_status_initial(self):
        """Test getting status before starting."""
        status = self.controller.get_status()
        
        assert status['is_running'] is False
        assert status['shutdown_requested'] is False
        assert status['uptime_seconds'] is None
        assert status['cycles_completed'] == 0
        assert status['images_generated'] == 0
        assert status['errors_encountered'] == 0
        assert status['consecutive_errors'] == 0
        assert status['audio_capture_active'] is False
        assert status['audio_queue_size'] == 0
        assert status['speech_processor_ready'] is False
    
    @patch('voxel.controller.AudioCapture')
    @patch('voxel.controller.SpeechProcessor')
    @patch('voxel.controller.TextAnalyzer')
    @patch('voxel.controller.PromptCrafter')
    @patch('voxel.controller.ImageGenerator')
    @patch('voxel.controller.DisplayController')
    def test_get_status_running(self, mock_display, mock_generator, mock_crafter, 
                               mock_analyzer, mock_speech, mock_audio):
        """Test getting status while running."""
        # Setup mocks
        mock_speech_instance = Mock()
        mock_speech_instance.initialize_model.return_value = True
        mock_speech_instance.is_initialized = True
        mock_speech.return_value = mock_speech_instance
        
        mock_audio_instance = Mock()
        mock_audio_instance.is_recording.return_value = True
        mock_audio_instance.get_queue_size.return_value = 3
        mock_audio.return_value = mock_audio_instance
        
        # Initialize and start
        self.controller.initialize_components()
        self.controller.stats['start_time'] = datetime.now()
        self.controller.is_running = True
        
        status = self.controller.get_status()
        
        assert status['is_running'] is True
        assert status['uptime_seconds'] is not None
        assert status['uptime_seconds'] >= 0
        assert status['audio_capture_active'] is True
        assert status['audio_queue_size'] == 3
        assert status['speech_processor_ready'] is True


class TestMainControllerProcessingCycle:
    """Test suite for MainController processing cycle functionality."""
    
    def setup_method(self):
        """Set up test fixtures with mocked components."""
        self.controller = MainController()
        
        # Create mock components
        self.mock_audio_capture = Mock()
        self.mock_speech_processor = Mock()
        self.mock_text_analyzer = Mock()
        self.mock_prompt_crafter = Mock()
        self.mock_image_generator = Mock()
        self.mock_display_controller = Mock()
        
        # Assign mocks to controller
        self.controller.audio_capture = self.mock_audio_capture
        self.controller.speech_processor = self.mock_speech_processor
        self.controller.text_analyzer = self.mock_text_analyzer
        self.controller.prompt_crafter = self.mock_prompt_crafter
        self.controller.image_generator = self.mock_image_generator
        self.controller.display_controller = self.mock_display_controller
    
    def teardown_method(self):
        """Clean up after tests."""
        if self.controller.is_running:
            self.controller.shutdown()
    
    def test_execute_processing_cycle_success(self):
        """Test successful processing cycle execution."""
        # Setup test data
        audio_chunk = AudioChunk(
            data=b"test_audio_data",
            timestamp=datetime.now(),
            duration=5.0,
            sample_rate=16000
        )
        
        transcription = TranscriptionResult(
            text="hello world test conversation",
            confidence=0.8,
            timestamp=datetime.now(),
            is_valid=True
        )
        
        analysis = AnalysisResult(
            keywords=["hello", "world", "test"],
            sentiment="positive",
            themes=["emotions"],
            confidence=0.7
        )
        
        prompt = ImagePrompt(
            prompt_text="A beautiful digital painting with warm colors",
            style_modifiers=["digital painting", "warm colors"],
            source_analysis=analysis,
            timestamp=datetime.now()
        )
        
        generated_image = GeneratedImage(
            url="https://example.com/image.png",
            local_path="/path/to/image.png",
            prompt=prompt,
            generation_time=datetime.now(),
            api_response={"success": True}
        )
        
        # Setup mock returns
        self.mock_audio_capture.is_recording.return_value = True
        self.mock_audio_capture.get_audio_chunk.return_value = audio_chunk
        self.mock_speech_processor.transcribe_audio.return_value = transcription
        self.mock_text_analyzer.analyze_text.return_value = analysis
        self.mock_prompt_crafter.craft_prompt.return_value = prompt
        self.mock_image_generator.generate_image.return_value = generated_image
        self.mock_display_controller.display_image.return_value = True
        
        # Execute cycle
        result = self.controller._execute_processing_cycle()
        
        # Verify success
        assert result is True
        assert self.controller.stats['images_generated'] == 1
        
        # Verify all components were called
        self.mock_audio_capture.get_audio_chunk.assert_called_once()
        self.mock_speech_processor.transcribe_audio.assert_called_once_with(audio_chunk)
        self.mock_text_analyzer.analyze_text.assert_called_once_with(transcription)
        self.mock_prompt_crafter.craft_prompt.assert_called_once_with(analysis)
        self.mock_image_generator.generate_image.assert_called_once_with(prompt)
        self.mock_display_controller.display_image.assert_called_once_with(generated_image)
    
    def test_execute_processing_cycle_no_audio(self):
        """Test processing cycle with no audio available."""
        # Setup mocks
        self.mock_audio_capture.is_recording.return_value = True
        self.mock_audio_capture.get_audio_chunk.return_value = None
        
        # Execute cycle
        result = self.controller._execute_processing_cycle()
        
        # Should succeed but not process anything
        assert result is True
        assert self.controller.stats['images_generated'] == 0
        
        # Only audio capture should be called
        self.mock_audio_capture.get_audio_chunk.assert_called_once()
        self.mock_speech_processor.transcribe_audio.assert_not_called()
    
    def test_execute_processing_cycle_invalid_speech(self):
        """Test processing cycle with invalid speech transcription."""
        # Setup test data
        audio_chunk = AudioChunk(
            data=b"test_audio_data",
            timestamp=datetime.now(),
            duration=5.0,
            sample_rate=16000
        )
        
        transcription = TranscriptionResult(
            text="",
            confidence=0.2,
            timestamp=datetime.now(),
            is_valid=False
        )
        
        # Setup mock returns
        self.mock_audio_capture.is_recording.return_value = True
        self.mock_audio_capture.get_audio_chunk.return_value = audio_chunk
        self.mock_speech_processor.transcribe_audio.return_value = transcription
        
        # Execute cycle
        result = self.controller._execute_processing_cycle()
        
        # Should succeed but not continue processing
        assert result is True
        assert self.controller.stats['images_generated'] == 0
        
        # Should stop after speech processing
        self.mock_speech_processor.transcribe_audio.assert_called_once()
        self.mock_text_analyzer.analyze_text.assert_not_called()
    
    def test_execute_processing_cycle_low_confidence_analysis(self):
        """Test processing cycle with low confidence analysis."""
        # Setup test data
        audio_chunk = AudioChunk(
            data=b"test_audio_data",
            timestamp=datetime.now(),
            duration=5.0,
            sample_rate=16000
        )
        
        transcription = TranscriptionResult(
            text="um uh",
            confidence=0.5,
            timestamp=datetime.now(),
            is_valid=True
        )
        
        analysis = AnalysisResult(
            keywords=[],
            sentiment="neutral",
            themes=[],
            confidence=0.1  # Very low confidence
        )
        
        # Setup mock returns
        self.mock_audio_capture.is_recording.return_value = True
        self.mock_audio_capture.get_audio_chunk.return_value = audio_chunk
        self.mock_speech_processor.transcribe_audio.return_value = transcription
        self.mock_text_analyzer.analyze_text.return_value = analysis
        
        # Execute cycle
        result = self.controller._execute_processing_cycle()
        
        # Should succeed but not continue processing
        assert result is True
        assert self.controller.stats['images_generated'] == 0
        
        # Should stop after text analysis
        self.mock_text_analyzer.analyze_text.assert_called_once()
        self.mock_prompt_crafter.craft_prompt.assert_not_called()
    
    def test_execute_processing_cycle_image_generation_failure(self):
        """Test processing cycle with image generation failure."""
        # Setup test data
        audio_chunk = AudioChunk(
            data=b"test_audio_data",
            timestamp=datetime.now(),
            duration=5.0,
            sample_rate=16000
        )
        
        transcription = TranscriptionResult(
            text="hello world test conversation",
            confidence=0.8,
            timestamp=datetime.now(),
            is_valid=True
        )
        
        analysis = AnalysisResult(
            keywords=["hello", "world"],
            sentiment="positive",
            themes=["emotions"],
            confidence=0.7
        )
        
        prompt = ImagePrompt(
            prompt_text="A beautiful digital painting",
            style_modifiers=["digital painting"],
            source_analysis=analysis,
            timestamp=datetime.now()
        )
        
        # Setup mock returns
        self.mock_audio_capture.is_recording.return_value = True
        self.mock_audio_capture.get_audio_chunk.return_value = audio_chunk
        self.mock_speech_processor.transcribe_audio.return_value = transcription
        self.mock_text_analyzer.analyze_text.return_value = analysis
        self.mock_prompt_crafter.craft_prompt.return_value = prompt
        self.mock_image_generator.generate_image.return_value = None  # Failure
        
        # Execute cycle
        result = self.controller._execute_processing_cycle()
        
        # Should fail
        assert result is False
        assert self.controller.stats['images_generated'] == 0
    
    def test_execute_processing_cycle_display_failure(self):
        """Test processing cycle with display failure."""
        # Setup test data (same as success test)
        audio_chunk = AudioChunk(
            data=b"test_audio_data",
            timestamp=datetime.now(),
            duration=5.0,
            sample_rate=16000
        )
        
        transcription = TranscriptionResult(
            text="hello world test conversation",
            confidence=0.8,
            timestamp=datetime.now(),
            is_valid=True
        )
        
        analysis = AnalysisResult(
            keywords=["hello", "world"],
            sentiment="positive",
            themes=["emotions"],
            confidence=0.7
        )
        
        prompt = ImagePrompt(
            prompt_text="A beautiful digital painting",
            style_modifiers=["digital painting"],
            source_analysis=analysis,
            timestamp=datetime.now()
        )
        
        generated_image = GeneratedImage(
            url="https://example.com/image.png",
            local_path="/path/to/image.png",
            prompt=prompt,
            generation_time=datetime.now(),
            api_response={"success": True}
        )
        
        # Setup mock returns
        self.mock_audio_capture.is_recording.return_value = True
        self.mock_audio_capture.get_audio_chunk.return_value = audio_chunk
        self.mock_speech_processor.transcribe_audio.return_value = transcription
        self.mock_text_analyzer.analyze_text.return_value = analysis
        self.mock_prompt_crafter.craft_prompt.return_value = prompt
        self.mock_image_generator.generate_image.return_value = generated_image
        self.mock_display_controller.display_image.return_value = False  # Display failure
        
        # Execute cycle
        result = self.controller._execute_processing_cycle()
        
        # Should still succeed (image was generated)
        assert result is True
        assert self.controller.stats['images_generated'] == 1


class TestMainControllerTimingAndShutdown:
    """Test suite for MainController timing and shutdown functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.controller = MainController()
    
    def teardown_method(self):
        """Clean up after tests."""
        if self.controller.is_running:
            self.controller.shutdown()
    
    def test_wait_for_cooldown_full_wait(self):
        """Test cooldown waiting when cycle completes quickly."""
        start_time = datetime.now()
        
        # Simulate quick cycle (should wait full cooldown)
        cycle_start = start_time
        
        # Mock the cooldown to be shorter for testing
        original_cooldown = SystemConfig.CYCLE_COOLDOWN
        SystemConfig.CYCLE_COOLDOWN = 2  # 2 seconds for testing
        
        try:
            self.controller._wait_for_cooldown(cycle_start)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            assert elapsed >= 1.8  # Allow some tolerance
            assert elapsed <= 2.5
        finally:
            SystemConfig.CYCLE_COOLDOWN = original_cooldown
    
    def test_wait_for_cooldown_no_wait(self):
        """Test cooldown when cycle takes longer than cooldown period."""
        # Simulate long cycle (no wait needed)
        cycle_start = datetime.now() - timedelta(seconds=35)  # 35 seconds ago
        
        start_time = datetime.now()
        self.controller._wait_for_cooldown(cycle_start)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Should return immediately
        assert elapsed < 0.1
    
    def test_wait_for_cooldown_with_shutdown(self):
        """Test cooldown interruption during shutdown."""
        # Set shutdown event
        self.controller._shutdown_event.set()
        
        start_time = datetime.now()
        cycle_start = start_time
        
        # Mock longer cooldown
        original_cooldown = SystemConfig.CYCLE_COOLDOWN
        SystemConfig.CYCLE_COOLDOWN = 5  # 5 seconds
        
        try:
            self.controller._wait_for_cooldown(cycle_start)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            # Should return quickly due to shutdown
            assert elapsed < 1.0
        finally:
            SystemConfig.CYCLE_COOLDOWN = original_cooldown
    
    def test_shutdown_not_running(self):
        """Test shutdown when not running."""
        assert not self.controller.is_running
        
        self.controller.shutdown()
        
        assert self.controller.shutdown_requested
        assert self.controller._shutdown_event.is_set()
    
    @patch('voxel.controller.AudioCapture')
    @patch('voxel.controller.SpeechProcessor')
    @patch('voxel.controller.TextAnalyzer')
    @patch('voxel.controller.PromptCrafter')
    @patch('voxel.controller.ImageGenerator')
    @patch('voxel.controller.DisplayController')
    def test_shutdown_with_cleanup(self, mock_display, mock_generator, mock_crafter, 
                                  mock_analyzer, mock_speech, mock_audio):
        """Test shutdown with component cleanup."""
        # Setup mocks
        mock_speech_instance = Mock()
        mock_speech_instance.initialize_model.return_value = True
        mock_speech_instance.cleanup = Mock()
        mock_speech.return_value = mock_speech_instance
        
        mock_audio_instance = Mock()
        mock_audio_instance.stop_recording = Mock()
        mock_audio.return_value = mock_audio_instance
        
        mock_display_instance = Mock()
        mock_display_instance.cleanup = Mock()
        mock_display.return_value = mock_display_instance
        
        mock_generator_instance = Mock()
        mock_generator_instance.cleanup_old_images = Mock()
        mock_generator.return_value = mock_generator_instance
        
        # Initialize components
        self.controller.initialize_components()
        self.controller.is_running = True
        
        # Shutdown
        self.controller.shutdown()
        
        # Verify cleanup was called
        mock_audio_instance.stop_recording.assert_called_once()
        mock_speech_instance.cleanup.assert_called_once()
        mock_display_instance.cleanup.assert_called_once()
        mock_generator_instance.cleanup_old_images.assert_called_once()
        
        assert not self.controller.is_running
        assert self.controller.shutdown_requested
    
    def test_handle_shutdown_signal(self):
        """Test handling shutdown signals."""
        assert not self.controller.shutdown_requested
        
        # Simulate signal handler
        self.controller.handle_shutdown(signum=2)  # SIGINT
        
        assert self.controller.shutdown_requested
        assert self.controller._shutdown_event.is_set()


class TestMainControllerErrorHandling:
    """Test suite for MainController error handling functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.controller = MainController()
    
    def teardown_method(self):
        """Clean up after tests."""
        if self.controller.is_running:
            self.controller.shutdown()
    
    def test_handle_cycle_error_tracking(self):
        """Test error tracking during cycle errors."""
        initial_error_count = self.controller.error_count
        initial_consecutive = self.controller.consecutive_errors
        
        self.controller._handle_cycle_error()
        
        assert self.controller.error_count == initial_error_count + 1
        assert self.controller.consecutive_errors == initial_consecutive + 1
        assert self.controller.stats['errors_encountered'] == initial_error_count + 1
    
    @patch('voxel.controller.AudioCapture')
    @patch('voxel.controller.DisplayController')
    def test_attempt_recovery(self, mock_display, mock_audio):
        """Test system recovery attempt."""
        # Setup mocks
        mock_audio_instance = Mock()
        mock_audio_instance.stop_recording = Mock()
        mock_audio_instance.start_recording = Mock()
        mock_audio.return_value = mock_audio_instance
        
        mock_display_instance = Mock()
        mock_display_instance.clear_display = Mock()
        mock_display.return_value = mock_display_instance
        
        # Assign mocks
        self.controller.audio_capture = mock_audio_instance
        self.controller.display_controller = mock_display_instance
        
        # Set high consecutive error count
        self.controller.consecutive_errors = 5
        
        # Attempt recovery
        self.controller._attempt_recovery()
        
        # Verify recovery actions
        mock_audio_instance.stop_recording.assert_called_once()
        mock_audio_instance.start_recording.assert_called_once()
        mock_display_instance.clear_display.assert_called_once()
        
        # Error count should be reset
        assert self.controller.consecutive_errors == 0
    
    def test_attempt_recovery_with_exceptions(self):
        """Test recovery attempt with component exceptions."""
        # Create mock that raises exception
        mock_audio = Mock()
        mock_audio.stop_recording.side_effect = Exception("Audio error")
        mock_audio.start_recording.side_effect = Exception("Audio error")
        
        self.controller.audio_capture = mock_audio
        self.controller.consecutive_errors = 5
        
        # Should not raise exception
        self.controller._attempt_recovery()
        
        # Error count should still be reset (recovery "attempted")
        assert self.controller.consecutive_errors == 0


@pytest.mark.integration
class TestMainControllerIntegration:
    """Integration tests for complete MainController workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.controller = MainController()
    
    def teardown_method(self):
        """Clean up after tests."""
        if self.controller.is_running:
            self.controller.shutdown()
    
    @patch('voxel.controller.AudioCapture')
    @patch('voxel.controller.SpeechProcessor')
    @patch('voxel.controller.TextAnalyzer')
    @patch('voxel.controller.PromptCrafter')
    @patch('voxel.controller.ImageGenerator')
    @patch('voxel.controller.DisplayController')
    def test_full_workflow_integration(self, mock_display, mock_generator, mock_crafter, 
                                     mock_analyzer, mock_speech, mock_audio):
        """Test complete workflow integration with all components."""
        # This test verifies that all components work together correctly
        # in a realistic scenario
        
        # Setup realistic test data
        audio_chunk = AudioChunk(
            data=b"realistic_audio_data_chunk",
            timestamp=datetime.now(),
            duration=5.0,
            sample_rate=16000
        )
        
        transcription = TranscriptionResult(
            text="I love the beautiful sunset colors tonight",
            confidence=0.85,
            timestamp=datetime.now(),
            is_valid=True
        )
        
        analysis = AnalysisResult(
            keywords=["love", "beautiful", "sunset", "colors", "tonight"],
            sentiment="positive",
            themes=["nature", "emotions"],
            confidence=0.8
        )
        
        prompt = ImagePrompt(
            prompt_text="A beautiful digital painting of a sunset with warm golden colors and peaceful atmosphere, high quality artistic composition",
            style_modifiers=["digital painting", "warm golden colors", "peaceful atmosphere", "high quality"],
            source_analysis=analysis,
            timestamp=datetime.now()
        )
        
        generated_image = GeneratedImage(
            url="https://api.openai.com/generated/sunset_image.png",
            local_path="generated_images/voxel_art_20240101_120000.png",
            prompt=prompt,
            generation_time=datetime.now(),
            api_response={"created": 1234567890, "data": [{"url": "https://api.openai.com/generated/sunset_image.png"}]}
        )
        
        # Setup component mocks with realistic behavior
        mock_speech_instance = Mock()
        mock_speech_instance.initialize_model.return_value = True
        mock_speech_instance.is_initialized = True
        mock_speech_instance.transcribe_audio.return_value = transcription
        mock_speech_instance.cleanup = Mock()
        mock_speech.return_value = mock_speech_instance
        
        mock_audio_instance = Mock()
        mock_audio_instance.start_recording = Mock()
        mock_audio_instance.stop_recording = Mock()
        mock_audio_instance.is_recording.return_value = True
        mock_audio_instance.get_audio_chunk.return_value = audio_chunk
        mock_audio_instance.get_queue_size.return_value = 2
        mock_audio.return_value = mock_audio_instance
        
        mock_analyzer_instance = Mock()
        mock_analyzer_instance.analyze_text.return_value = analysis
        mock_analyzer.return_value = mock_analyzer_instance
        
        mock_crafter_instance = Mock()
        mock_crafter_instance.craft_prompt.return_value = prompt
        mock_crafter.return_value = mock_crafter_instance
        
        mock_generator_instance = Mock()
        mock_generator_instance.generate_image.return_value = generated_image
        mock_generator_instance.cleanup_old_images = Mock()
        mock_generator.return_value = mock_generator_instance
        
        mock_display_instance = Mock()
        mock_display_instance.display_image.return_value = True
        mock_display_instance.cleanup = Mock()
        mock_display.return_value = mock_display_instance
        
        # Test complete workflow
        # 1. Initialize components
        assert self.controller.initialize_components() is True
        
        # 2. Execute one processing cycle
        result = self.controller._execute_processing_cycle()
        assert result is True
        
        # 3. Verify all components were called in correct order
        mock_audio_instance.get_audio_chunk.assert_called_once()
        mock_speech_instance.transcribe_audio.assert_called_once_with(audio_chunk)
        mock_analyzer_instance.analyze_text.assert_called_once_with(transcription)
        mock_crafter_instance.craft_prompt.assert_called_once_with(analysis)
        mock_generator_instance.generate_image.assert_called_once_with(prompt)
        mock_display_instance.display_image.assert_called_once_with(generated_image)
        
        # 4. Verify statistics were updated
        assert self.controller.stats['images_generated'] == 1
        
        # 5. Test status reporting
        status = self.controller.get_status()
        assert status['audio_capture_active'] is True
        assert status['speech_processor_ready'] is True
        assert status['audio_queue_size'] == 2
        
        # 6. Test graceful shutdown
        self.controller.shutdown()
        
        # Verify cleanup was called
        mock_audio_instance.stop_recording.assert_called_once()
        mock_speech_instance.cleanup.assert_called_once()
        mock_display_instance.cleanup.assert_called_once()
        mock_generator_instance.cleanup_old_images.assert_called_once()
        
        assert not self.controller.is_running
        assert self.controller.shutdown_requested