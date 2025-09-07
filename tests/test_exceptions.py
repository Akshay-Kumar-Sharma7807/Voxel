"""
Unit tests for custom exception classes.
"""

import pytest
from voxel.exceptions import (
    VoxelError, AudioCaptureError, MicrophoneNotFoundError, 
    AudioPermissionError, AudioBufferOverflowError,
    SpeechProcessingError, ModelLoadError, TranscriptionError, 
    LowConfidenceError, TextAnalysisError, KeywordExtractionError,
    SentimentAnalysisError, ImageGenerationError, APIConnectionError,
    APIRateLimitError, APIAuthenticationError, InvalidPromptError,
    ImageDownloadError, DisplayError, DisplayCommandError,
    ImageProcessingError, ScreenNotFoundError, SystemError,
    ConfigurationError, DependencyError, ResourceError
)


class TestVoxelError:
    """Test cases for base VoxelError class."""
    
    def test_basic_error_creation(self):
        """Test creating a basic VoxelError."""
        error = VoxelError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.component is None
        assert error.additional_data == {}
    
    def test_error_with_component(self):
        """Test VoxelError with component information."""
        error = VoxelError("Test error", component="TestComponent")
        
        assert str(error) == "Test error"
        assert error.component == "TestComponent"
        assert error.additional_data == {}
    
    def test_error_with_additional_data(self):
        """Test VoxelError with additional data."""
        additional_data = {
            "operation": "test_operation",
            "timestamp": "2024-01-01T00:00:00",
            "retry_count": 3
        }
        
        error = VoxelError(
            "Test error with data",
            component="TestComponent",
            additional_data=additional_data
        )
        
        assert str(error) == "Test error with data"
        assert error.component == "TestComponent"
        assert error.additional_data == additional_data
        assert error.additional_data["operation"] == "test_operation"
        assert error.additional_data["retry_count"] == 3
    
    def test_error_inheritance(self):
        """Test that VoxelError inherits from Exception."""
        error = VoxelError("Test error")
        
        assert isinstance(error, Exception)
        assert isinstance(error, VoxelError)


class TestAudioErrors:
    """Test cases for audio-related exception classes."""
    
    def test_audio_capture_error(self):
        """Test AudioCaptureError creation and inheritance."""
        error = AudioCaptureError("Audio capture failed")
        
        assert isinstance(error, VoxelError)
        assert isinstance(error, AudioCaptureError)
        assert str(error) == "Audio capture failed"
    
    def test_microphone_not_found_error(self):
        """Test MicrophoneNotFoundError."""
        error = MicrophoneNotFoundError(
            "No microphone detected",
            component="AudioCapture",
            additional_data={"available_devices": 0}
        )
        
        assert isinstance(error, AudioCaptureError)
        assert isinstance(error, VoxelError)
        assert str(error) == "No microphone detected"
        assert error.component == "AudioCapture"
        assert error.additional_data["available_devices"] == 0
    
    def test_audio_permission_error(self):
        """Test AudioPermissionError."""
        error = AudioPermissionError("Microphone access denied")
        
        assert isinstance(error, AudioCaptureError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Microphone access denied"
    
    def test_audio_buffer_overflow_error(self):
        """Test AudioBufferOverflowError."""
        error = AudioBufferOverflowError(
            "Audio buffer overflow",
            additional_data={"buffer_size": 1024, "overflow_count": 5}
        )
        
        assert isinstance(error, AudioCaptureError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Audio buffer overflow"
        assert error.additional_data["buffer_size"] == 1024
        assert error.additional_data["overflow_count"] == 5


class TestSpeechErrors:
    """Test cases for speech processing exception classes."""
    
    def test_speech_processing_error(self):
        """Test SpeechProcessingError creation and inheritance."""
        error = SpeechProcessingError("Speech processing failed")
        
        assert isinstance(error, VoxelError)
        assert isinstance(error, SpeechProcessingError)
        assert str(error) == "Speech processing failed"
    
    def test_model_load_error(self):
        """Test ModelLoadError."""
        error = ModelLoadError(
            "Failed to load Vosk model",
            component="SpeechProcessor",
            additional_data={"model_path": "/path/to/model", "model_size": "91MB"}
        )
        
        assert isinstance(error, SpeechProcessingError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Failed to load Vosk model"
        assert error.component == "SpeechProcessor"
        assert error.additional_data["model_path"] == "/path/to/model"
    
    def test_transcription_error(self):
        """Test TranscriptionError."""
        error = TranscriptionError("Transcription failed")
        
        assert isinstance(error, SpeechProcessingError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Transcription failed"
    
    def test_low_confidence_error(self):
        """Test LowConfidenceError."""
        error = LowConfidenceError(
            "Transcription confidence too low",
            additional_data={"confidence": 0.2, "threshold": 0.5}
        )
        
        assert isinstance(error, SpeechProcessingError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Transcription confidence too low"
        assert error.additional_data["confidence"] == 0.2
        assert error.additional_data["threshold"] == 0.5


class TestTextAnalysisErrors:
    """Test cases for text analysis exception classes."""
    
    def test_text_analysis_error(self):
        """Test TextAnalysisError creation and inheritance."""
        error = TextAnalysisError("Text analysis failed")
        
        assert isinstance(error, VoxelError)
        assert isinstance(error, TextAnalysisError)
        assert str(error) == "Text analysis failed"
    
    def test_keyword_extraction_error(self):
        """Test KeywordExtractionError."""
        error = KeywordExtractionError(
            "Keyword extraction failed",
            component="TextAnalyzer",
            additional_data={"text_length": 150, "method": "frequency"}
        )
        
        assert isinstance(error, TextAnalysisError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Keyword extraction failed"
        assert error.component == "TextAnalyzer"
        assert error.additional_data["method"] == "frequency"
    
    def test_sentiment_analysis_error(self):
        """Test SentimentAnalysisError."""
        error = SentimentAnalysisError("Sentiment analysis failed")
        
        assert isinstance(error, TextAnalysisError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Sentiment analysis failed"


class TestImageGenerationErrors:
    """Test cases for image generation exception classes."""
    
    def test_image_generation_error(self):
        """Test ImageGenerationError creation and inheritance."""
        error = ImageGenerationError("Image generation failed")
        
        assert isinstance(error, VoxelError)
        assert isinstance(error, ImageGenerationError)
        assert str(error) == "Image generation failed"
    
    def test_api_connection_error(self):
        """Test APIConnectionError."""
        error = APIConnectionError(
            "Failed to connect to API",
            component="ImageGenerator",
            additional_data={"endpoint": "https://api.openai.com", "timeout": 30}
        )
        
        assert isinstance(error, ImageGenerationError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Failed to connect to API"
        assert error.component == "ImageGenerator"
        assert error.additional_data["endpoint"] == "https://api.openai.com"
    
    def test_api_rate_limit_error(self):
        """Test APIRateLimitError."""
        error = APIRateLimitError(
            "API rate limit exceeded",
            additional_data={"retry_after": 60, "requests_remaining": 0}
        )
        
        assert isinstance(error, ImageGenerationError)
        assert isinstance(error, VoxelError)
        assert str(error) == "API rate limit exceeded"
        assert error.additional_data["retry_after"] == 60
    
    def test_api_authentication_error(self):
        """Test APIAuthenticationError."""
        error = APIAuthenticationError("Invalid API key")
        
        assert isinstance(error, ImageGenerationError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Invalid API key"
    
    def test_invalid_prompt_error(self):
        """Test InvalidPromptError."""
        error = InvalidPromptError(
            "Prompt violates content policy",
            additional_data={"prompt": "inappropriate content", "policy": "safety"}
        )
        
        assert isinstance(error, ImageGenerationError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Prompt violates content policy"
        assert error.additional_data["prompt"] == "inappropriate content"
    
    def test_image_download_error(self):
        """Test ImageDownloadError."""
        error = ImageDownloadError(
            "Failed to download image",
            additional_data={"url": "https://example.com/image.png", "status_code": 404}
        )
        
        assert isinstance(error, ImageGenerationError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Failed to download image"
        assert error.additional_data["status_code"] == 404


class TestDisplayErrors:
    """Test cases for display exception classes."""
    
    def test_display_error(self):
        """Test DisplayError creation and inheritance."""
        error = DisplayError("Display operation failed")
        
        assert isinstance(error, VoxelError)
        assert isinstance(error, DisplayError)
        assert str(error) == "Display operation failed"
    
    def test_display_command_error(self):
        """Test DisplayCommandError."""
        error = DisplayCommandError(
            "Display command failed",
            component="DisplayController",
            additional_data={"command": "fbi", "exit_code": 1}
        )
        
        assert isinstance(error, DisplayError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Display command failed"
        assert error.component == "DisplayController"
        assert error.additional_data["command"] == "fbi"
    
    def test_image_processing_error(self):
        """Test ImageProcessingError."""
        error = ImageProcessingError(
            "Image preprocessing failed",
            additional_data={"image_path": "/path/to/image.png", "operation": "resize"}
        )
        
        assert isinstance(error, DisplayError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Image preprocessing failed"
        assert error.additional_data["operation"] == "resize"
    
    def test_screen_not_found_error(self):
        """Test ScreenNotFoundError."""
        error = ScreenNotFoundError("No display screen detected")
        
        assert isinstance(error, DisplayError)
        assert isinstance(error, VoxelError)
        assert str(error) == "No display screen detected"


class TestSystemErrors:
    """Test cases for system exception classes."""
    
    def test_system_error(self):
        """Test SystemError creation and inheritance."""
        error = SystemError("System operation failed")
        
        assert isinstance(error, VoxelError)
        assert isinstance(error, SystemError)
        assert str(error) == "System operation failed"
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError(
            "Invalid configuration",
            component="SystemConfig",
            additional_data={"missing_keys": ["API_KEY", "MODEL_PATH"]}
        )
        
        assert isinstance(error, SystemError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Invalid configuration"
        assert error.component == "SystemConfig"
        assert "API_KEY" in error.additional_data["missing_keys"]
    
    def test_dependency_error(self):
        """Test DependencyError."""
        error = DependencyError(
            "Required dependency not found",
            additional_data={"dependency": "vosk", "version": "0.3.45"}
        )
        
        assert isinstance(error, SystemError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Required dependency not found"
        assert error.additional_data["dependency"] == "vosk"
    
    def test_resource_error(self):
        """Test ResourceError."""
        error = ResourceError(
            "Insufficient system resources",
            additional_data={"memory_usage": "95%", "cpu_usage": "98%"}
        )
        
        assert isinstance(error, SystemError)
        assert isinstance(error, VoxelError)
        assert str(error) == "Insufficient system resources"
        assert error.additional_data["memory_usage"] == "95%"


class TestErrorChaining:
    """Test cases for exception chaining and context."""
    
    def test_exception_chaining(self):
        """Test that exceptions can be properly chained."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise AudioCaptureError("Wrapped error") from e
        except AudioCaptureError as wrapped_error:
            assert str(wrapped_error) == "Wrapped error"
            assert isinstance(wrapped_error.__cause__, ValueError)
            assert str(wrapped_error.__cause__) == "Original error"
    
    def test_exception_context_preservation(self):
        """Test that exception context is preserved."""
        try:
            try:
                raise ValueError("Context error")
            except ValueError:
                raise SpeechProcessingError("New error")
        except SpeechProcessingError as new_error:
            assert str(new_error) == "New error"
            assert isinstance(new_error.__context__, ValueError)
            assert str(new_error.__context__) == "Context error"


class TestErrorStringRepresentation:
    """Test cases for error string representations."""
    
    def test_error_str_method(self):
        """Test that __str__ method works correctly."""
        error = AudioCaptureError("Test error message")
        assert str(error) == "Test error message"
    
    def test_error_repr_method(self):
        """Test that __repr__ method works correctly."""
        error = AudioCaptureError("Test error")
        repr_str = repr(error)
        
        assert "AudioCaptureError" in repr_str
        assert "Test error" in repr_str
    
    def test_error_with_unicode(self):
        """Test error handling with unicode characters."""
        error = TextAnalysisError("Error with unicode: café, naïve, résumé")
        assert "café" in str(error)
        assert "naïve" in str(error)
        assert "résumé" in str(error)


if __name__ == "__main__":
    pytest.main([__file__])