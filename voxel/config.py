"""
Configuration module for system constants and settings.
"""

import os
from pathlib import Path


class AudioConfig:
    """Audio capture configuration."""
    SAMPLE_RATE = 16000  # Hz, optimal for Vosk
    CHUNK_DURATION = 5.0  # seconds
    CHANNELS = 1  # mono
    FORMAT_BITS = 16
    BUFFER_SIZE = 1024
    RETRY_INTERVAL = 10  # seconds for microphone reconnection


class SpeechConfig:
    """Speech recognition configuration."""
    MODEL_NAME = "vosk-model-small-en-us-0.15"
    MODEL_SIZE = 91  # MB
    CONFIDENCE_THRESHOLD = 0.5
    ENABLE_PARTIAL_RESULTS = False


class AnalysisConfig:
    """Text analysis configuration."""
    MIN_KEYWORD_LENGTH = 3
    MAX_KEYWORDS = 10
    SENTIMENT_THRESHOLD = 0.3
    THEME_CATEGORIES = [
        "nature", "emotions", "activities", "objects", 
        "colors", "weather", "music", "technology"
    ]


class GenerationConfig:
    """Image generation configuration."""
    # Provider selection: "openai", "google_cloud", or "freepik"
    PROVIDER = os.getenv("IMAGE_PROVIDER", "freepik")
    
    # OpenAI DALL-E configuration
    DALLE_MODEL = "dall-e-3"
    OPENAI_IMAGE_SIZE = "1024x1024"
    OPENAI_STYLE = "natural"
    OPENAI_RESPONSE_FORMAT = "url"
    
    # Google Cloud Vertex AI configuration
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
    IMAGEN_MODEL = "imagegeneration@006"  # Latest Imagen model
    GCP_IMAGE_SIZE = 1024
    GCP_ASPECT_RATIO = "1:1"
    GCP_GUIDANCE_SCALE = 60  # Controls adherence to prompt
    GCP_SEED = None  # For reproducible results, set to integer
    
    # Freepik AI configuration (based on actual API structure)
    FREEPIK_API_KEY = os.getenv("FREEPIK_API_KEY")
    FREEPIK_BASE_URL = "https://api.freepik.com/v1"
    FREEPIK_IMAGE_SIZE = "square_1_1"  # square_1_1, portrait_3_4, portrait_9_16, landscape_4_3, landscape_16_9
    FREEPIK_STYLE = "photo"  # photo, digital-art, painting, illustration, anime
    FREEPIK_LIGHTING = "warm"  # warm, cold, studio, ambient, neon
    FREEPIK_FRAMING = "portrait"  # portrait, landscape, close-up, medium, full-body
    FREEPIK_GUIDANCE_SCALE = 2.0  # 1-20, higher = more adherence to prompt
    FREEPIK_COLOR_EFFECT = "vibrant"  # vibrant, pastel, monochrome
    
    # Common settings
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds


class DisplayConfig:
    """Display configuration."""
    DISPLAY_METHOD_PRIMARY = "fbi"  # framebuffer imageviewer
    DISPLAY_METHOD_FALLBACK = "pygame"
    FULLSCREEN = True
    IMAGE_CACHE_DIR = "generated_images"


class SystemConfig:
    """System-wide configuration."""
    CYCLE_COOLDOWN = 30  # seconds between processing cycles
    LOG_LEVEL = "INFO"
    LOG_FILE = "voxel.log"
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Environment variables
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    FREEPIK_API_KEY = os.getenv("FREEPIK_API_KEY")
    
    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent
    MODELS_DIR = PROJECT_ROOT / "models"
    IMAGES_DIR = PROJECT_ROOT / DisplayConfig.IMAGE_CACHE_DIR
    LOGS_DIR = PROJECT_ROOT / "logs"


class ErrorConfig:
    """Error handling configuration."""
    MAX_CONSECUTIVE_ERRORS = 5
    ERROR_RECOVERY_DELAY = 2  # seconds
    CRITICAL_ERROR_EXIT = True
    
    # Error categories
    RECOVERABLE_ERRORS = [
        "AudioCaptureError",
        "TranscriptionError", 
        "APIRateLimitError",
        "DisplayError"
    ]
    
    CRITICAL_ERRORS = [
        "ModelLoadError",
        "AuthenticationError",
        "ConfigurationError"
    ]