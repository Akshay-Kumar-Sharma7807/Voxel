"""
Core data models for the Voxel ambient art generator.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any


@dataclass
class AudioChunk:
    """Represents a captured audio segment."""
    data: bytes
    timestamp: datetime
    duration: float
    sample_rate: int


@dataclass
class TranscriptionResult:
    """Result of speech-to-text processing."""
    text: str
    confidence: float
    timestamp: datetime
    is_valid: bool


@dataclass
class AnalysisResult:
    """Result of text analysis including keywords and sentiment."""
    keywords: List[str]
    sentiment: str  # 'positive', 'negative', 'neutral'
    themes: List[str]
    confidence: float


@dataclass
class ImagePrompt:
    """Crafted prompt for image generation."""
    prompt_text: str
    style_modifiers: List[str]
    source_analysis: AnalysisResult
    timestamp: datetime


@dataclass
class GeneratedImage:
    """Information about a generated image."""
    url: str
    local_path: str
    prompt: ImagePrompt
    generation_time: datetime
    api_response: Dict[str, Any]