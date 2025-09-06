"""
Speech processing module for Voxel ambient art generator.
"""

from .processor import SpeechProcessor, SpeechProcessorError, ModelLoadError, TranscriptionError

__all__ = [
    'SpeechProcessor',
    'SpeechProcessorError', 
    'ModelLoadError',
    'TranscriptionError'
]