"""
Custom exception classes for Voxel components.
"""

from typing import Optional, Dict, Any


class VoxelError(Exception):
    """Base exception class for Voxel-specific errors."""
    
    def __init__(self, message: str, component: str = None, additional_data: Dict[str, Any] = None):
        super().__init__(message)
        self.component = component
        self.additional_data = additional_data or {}


class AudioCaptureError(VoxelError):
    """Raised when audio capture fails."""
    pass


class MicrophoneNotFoundError(AudioCaptureError):
    """Raised when no microphone is detected."""
    pass


class AudioPermissionError(AudioCaptureError):
    """Raised when microphone permissions are denied."""
    pass


class AudioBufferOverflowError(AudioCaptureError):
    """Raised when audio buffer overflows."""
    pass


class SpeechProcessingError(VoxelError):
    """Raised when speech-to-text processing fails."""
    pass


class ModelLoadError(SpeechProcessingError):
    """Raised when Vosk model fails to load."""
    pass


class TranscriptionError(SpeechProcessingError):
    """Raised when transcription fails."""
    pass


class LowConfidenceError(SpeechProcessingError):
    """Raised when transcription confidence is too low."""
    pass


class TextAnalysisError(VoxelError):
    """Raised when text analysis fails."""
    pass


class KeywordExtractionError(TextAnalysisError):
    """Raised when keyword extraction fails."""
    pass


class SentimentAnalysisError(TextAnalysisError):
    """Raised when sentiment analysis fails."""
    pass


class ImageGenerationError(VoxelError):
    """Raised when image generation fails."""
    pass


class APIConnectionError(ImageGenerationError):
    """Raised when API connection fails."""
    pass


class APIRateLimitError(ImageGenerationError):
    """Raised when API rate limit is exceeded."""
    pass


class APIAuthenticationError(ImageGenerationError):
    """Raised when API authentication fails."""
    pass


class InvalidPromptError(ImageGenerationError):
    """Raised when image prompt is invalid."""
    pass


class ImageDownloadError(ImageGenerationError):
    """Raised when image download fails."""
    pass


class DisplayError(VoxelError):
    """Raised when display operations fail."""
    pass


class DisplayCommandError(DisplayError):
    """Raised when display command execution fails."""
    pass


class ImageProcessingError(DisplayError):
    """Raised when image preprocessing fails."""
    pass


class ScreenNotFoundError(DisplayError):
    """Raised when no display screen is found."""
    pass


class SystemError(VoxelError):
    """Raised for general system errors."""
    pass


class ConfigurationError(SystemError):
    """Raised when configuration is invalid."""
    pass


class DependencyError(SystemError):
    """Raised when required dependencies are missing."""
    pass


class ResourceError(SystemError):
    """Raised when system resources are unavailable."""
    pass