"""
Speech-to-text processing using Vosk for on-device transcription.
"""

import json
from pathlib import Path
from typing import Optional

import vosk

from ..models import AudioChunk, TranscriptionResult
from ..config import SpeechConfig, SystemConfig, AudioConfig
from ..error_handler import ErrorCategory, ErrorSeverity, log_system_event
from ..exceptions import (
    SpeechProcessingError, ModelLoadError, TranscriptionError, LowConfidenceError
)
from ..decorators import handle_errors, log_operation, retry_on_error


class SpeechProcessor:
    """
    Handles speech-to-text processing using Vosk model for privacy-focused
    on-device transcription.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the speech processor.
        
        Args:
            model_path: Optional path to Vosk model directory. If None, uses default.
        """
        self.model = None
        self.recognizer = None
        self.model_path = model_path or self._get_default_model_path()
        self.is_initialized = False
        
    def _get_default_model_path(self) -> str:
        """Get the default path for the Vosk model."""
        return str(SystemConfig.MODELS_DIR / SpeechConfig.MODEL_NAME)
    
    @handle_errors(
        category=ErrorCategory.SPEECH_PROCESSING,
        severity=ErrorSeverity.CRITICAL,
        raise_on_critical=True
    )
    @log_operation(level="INFO")
    def initialize_model(self) -> bool:
        """
        Load and initialize the Vosk model.
        
        Returns:
            bool: True if initialization successful
            
        Raises:
            ModelLoadError: If model loading fails
        """
        log_system_event(f"Loading Vosk model from: {self.model_path}")
        
        # Check if model directory exists
        if not Path(self.model_path).exists():
            raise ModelLoadError(
                f"Vosk model not found at: {self.model_path}. "
                "Please download the model using: python -m vosk download-model",
                component="SpeechProcessor",
                additional_data={"model_path": self.model_path}
            )
        
        # Initialize Vosk model
        self.model = vosk.Model(self.model_path)
        self.recognizer = vosk.KaldiRecognizer(
            self.model, 
            AudioConfig.SAMPLE_RATE
        )
        
        # Configure recognizer
        self.recognizer.SetMaxAlternatives(1)
        self.recognizer.SetWords(True)
        
        self.is_initialized = True
        log_system_event("Vosk model initialized successfully")
        return True
    
    @handle_errors(
        category=ErrorCategory.SPEECH_PROCESSING,
        severity=ErrorSeverity.MEDIUM,
        return_on_error=None
    )
    def transcribe_audio(self, audio_chunk: AudioChunk) -> TranscriptionResult:
        """
        Transcribe an audio chunk to text.
        
        Args:
            audio_chunk: AudioChunk containing audio data to transcribe.
            
        Returns:
            TranscriptionResult: Transcription result with confidence score.
            
        Raises:
            TranscriptionError: If transcription fails
        """
        if not self.is_initialized:
            raise TranscriptionError(
                "Speech processor not initialized",
                component="SpeechProcessor",
                additional_data={"model_path": self.model_path}
            )
        
        # Convert audio data to the format expected by Vosk
        audio_data = self._prepare_audio_data(audio_chunk)
        
        # Process audio through recognizer
        if self.recognizer.AcceptWaveform(audio_data):
            result = json.loads(self.recognizer.Result())
        else:
            # Get partial result if no complete phrase detected
            result = json.loads(self.recognizer.PartialResult())
        
        # Extract text and confidence
        text = result.get('text', '').strip()
        confidence = self._calculate_confidence(result)
        
        # Validate the transcription
        is_valid = self.is_speech_detected(text, confidence)
        
        log_system_event(
            f"Transcribed: '{text}' (confidence: {confidence:.2f})",
            level="DEBUG",
            is_valid=is_valid
        )
        
        return TranscriptionResult(
            text=text,
            confidence=confidence,
            timestamp=audio_chunk.timestamp,
            is_valid=is_valid
        )
    
    def _prepare_audio_data(self, audio_chunk: AudioChunk) -> bytes:
        """
        Prepare audio data for Vosk processing.
        
        Args:
            audio_chunk: AudioChunk with raw audio data.
            
        Returns:
            bytes: Audio data in format expected by Vosk.
        """
        # Vosk expects 16-bit PCM audio data
        # If audio_chunk.data is already in the correct format, return as-is
        return audio_chunk.data
    
    def _calculate_confidence(self, result: dict) -> float:
        """
        Calculate confidence score from Vosk result.
        
        Args:
            result: Vosk recognition result dictionary.
            
        Returns:
            float: Confidence score between 0.0 and 1.0.
        """
        # Vosk provides confidence in the 'result' field for individual words
        if 'result' in result and result['result']:
            # Calculate average confidence from word-level confidences
            confidences = [word.get('conf', 0.0) for word in result['result']]
            if confidences:
                return sum(confidences) / len(confidences)
        
        # Fallback: estimate confidence based on text length and content
        text = result.get('text', '')
        if not text:
            return 0.0
        
        # Simple heuristic: longer, more complete sentences get higher confidence
        word_count = len(text.split())
        if word_count >= 3:
            return 0.8
        elif word_count >= 2:
            return 0.6
        elif word_count >= 1:
            return 0.4
        else:
            return 0.0
    
    def is_speech_detected(self, text: str, confidence: float) -> bool:
        """
        Validate if the transcription represents meaningful speech.
        
        Args:
            text: Transcribed text.
            confidence: Confidence score.
            
        Returns:
            bool: True if speech is detected and valid, False otherwise.
        """
        # Check confidence threshold
        if confidence < SpeechConfig.CONFIDENCE_THRESHOLD:
            log_system_event(
                f"Low confidence transcription rejected: {confidence:.2f}",
                level="DEBUG",
                threshold=SpeechConfig.CONFIDENCE_THRESHOLD
            )
            return False
        
        # Check text content
        if not text or len(text.strip()) == 0:
            log_system_event("Empty transcription rejected", level="DEBUG")
            return False
        
        # Check minimum word count (avoid single-word false positives)
        words = text.strip().split()
        if len(words) < 2:
            log_system_event(
                f"Too few words in transcription: {len(words)}",
                level="DEBUG",
                word_count=len(words)
            )
            return False
        
        # Check for common false positive patterns
        false_positives = ['uh', 'um', 'ah', 'er', 'hm', 'hmm']
        if all(word.lower() in false_positives for word in words):
            log_system_event("Transcription contains only filler words", level="DEBUG")
            return False
        
        log_system_event(f"Valid speech detected: '{text}'", level="DEBUG")
        return True
    
    @log_operation(level="INFO")
    def cleanup(self):
        """Clean up resources used by the speech processor."""
        if self.recognizer:
            # Vosk recognizer doesn't need explicit cleanup
            self.recognizer = None
        
        if self.model:
            # Vosk model doesn't need explicit cleanup
            self.model = None
        
        self.is_initialized = False
        log_system_event("Speech processor cleaned up")