"""
Image generation module supporting both OpenAI DALL-E and Google Cloud Vertex AI.
"""

import os
import time
import logging
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import requests

from ..models import ImagePrompt, GeneratedImage
from ..config import GenerationConfig, SystemConfig, ErrorConfig


logger = logging.getLogger(__name__)


class ImageGenerationError(Exception):
    """Base exception for image generation errors."""
    pass


class APIAuthenticationError(ImageGenerationError):
    """Raised when API authentication fails."""
    pass


class APIRateLimitError(ImageGenerationError):
    """Raised when API rate limit is exceeded."""
    pass


class ImageDownloadError(ImageGenerationError):
    """Raised when image download fails."""
    pass


class ImageGenerator:
    """
    Handles image generation using multiple providers (OpenAI DALL-E, Google Cloud Vertex AI, Freepik AI).
    """
    
    def __init__(self, provider: Optional[str] = None, **kwargs):
        """
        Initialize the ImageGenerator.
        
        Args:
            provider: Image generation provider ("openai", "google_cloud", or "freepik")
            **kwargs: Provider-specific configuration
        """
        self.provider = provider or GenerationConfig.PROVIDER
        self.images_dir = SystemConfig.IMAGES_DIR
        self.images_dir.mkdir(exist_ok=True)
        
        # Initialize the appropriate client
        if self.provider == "openai":
            self._init_openai_client(**kwargs)
        elif self.provider == "google_cloud":
            self._init_google_cloud_client(**kwargs)
        elif self.provider == "freepik":
            self._init_freepik_client(**kwargs)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        
        logger.info(f"ImageGenerator initialized successfully with {self.provider} provider")
    
    def _init_openai_client(self, api_key: Optional[str] = None):
        """Initialize OpenAI client."""
        from openai import OpenAI
        
        self.api_key = api_key or SystemConfig.OPENAI_API_KEY
        if not self.api_key:
            raise APIAuthenticationError("OpenAI API key not found in environment variables")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def _init_google_cloud_client(self, project_id: Optional[str] = None, location: Optional[str] = None):
        """Initialize Google Cloud Vertex AI client."""
        try:
            from google.cloud import aiplatform
            from vertexai.preview.vision_models import ImageGenerationModel
            
            self.project_id = project_id or GenerationConfig.GCP_PROJECT_ID
            self.location = location or GenerationConfig.GCP_LOCATION
            
            if not self.project_id:
                raise APIAuthenticationError("GCP_PROJECT_ID not found in environment variables")
            
            # Initialize Vertex AI
            aiplatform.init(project=self.project_id, location=self.location)
            
            # Load the Imagen model
            self.model = ImageGenerationModel.from_pretrained(GenerationConfig.IMAGEN_MODEL)
            
        except ImportError:
            raise ImportError(
                "Google Cloud libraries not installed. Install with: "
                "pip install google-cloud-aiplatform vertexai"
            )
        except Exception as e:
            raise APIAuthenticationError(f"Failed to initialize Google Cloud client: {e}")
    
    def _init_freepik_client(self, api_key: Optional[str] = None):
        """Initialize Freepik API client."""
        self.freepik_api_key = api_key or GenerationConfig.FREEPIK_API_KEY
        if not self.freepik_api_key:
            raise APIAuthenticationError("Freepik API key not found in environment variables")
        
        self.freepik_headers = {
            "X-Freepik-API-Key": self.freepik_api_key,
            "Content-Type": "application/json"
        }
    
    def generate_image(self, prompt: ImagePrompt) -> GeneratedImage:
        """
        Generate an image using the configured provider with retry logic.
        
        Args:
            prompt: ImagePrompt containing the text prompt and metadata
            
        Returns:
            GeneratedImage with URL, local path, and metadata
            
        Raises:
            ImageGenerationError: If generation fails after all retries
        """
        logger.info(f"Starting image generation with {self.provider} for prompt: {prompt.prompt_text[:100]}...")
        
        for attempt in range(GenerationConfig.MAX_RETRIES):
            try:
                if self.provider == "openai":
                    response = self._make_openai_call(prompt.prompt_text)
                    image_url = response['data'][0]['url']
                    local_path = self._download_image(image_url, prompt.timestamp)
                    
                    generated_image = GeneratedImage(
                        url=image_url,
                        local_path=str(local_path),
                        prompt=prompt,
                        generation_time=datetime.now(),
                        api_response=response
                    )
                    
                elif self.provider == "google_cloud":
                    response = self._make_google_cloud_call(prompt.prompt_text)
                    local_path = self._save_google_cloud_image(response, prompt.timestamp)
                    
                    generated_image = GeneratedImage(
                        url="",  # Google Cloud returns base64, not URL
                        local_path=str(local_path),
                        prompt=prompt,
                        generation_time=datetime.now(),
                        api_response={"provider": "google_cloud", "success": True}
                    )
                
                elif self.provider == "freepik":
                    response = self._make_freepik_call(prompt.prompt_text)
                    local_path = self._save_freepik_image(response, prompt.timestamp)
                    
                    generated_image = GeneratedImage(
                        url="",  # Freepik returns base64, not URL
                        local_path=str(local_path),
                        prompt=prompt,
                        generation_time=datetime.now(),
                        api_response=response
                    )
                
                logger.info(f"Image saved to: {local_path}")
                return generated_image
                
            except APIRateLimitError as e:
                logger.warning(f"Rate limit hit on attempt {attempt + 1}: {e}")
                if attempt < GenerationConfig.MAX_RETRIES - 1:
                    wait_time = GenerationConfig.RETRY_DELAY * (2 ** attempt)
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    raise ImageGenerationError(f"Failed to generate image after {GenerationConfig.MAX_RETRIES} attempts due to rate limiting")
            
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < GenerationConfig.MAX_RETRIES - 1:
                    time.sleep(GenerationConfig.RETRY_DELAY)
                else:
                    raise ImageGenerationError(f"Failed to generate image after {GenerationConfig.MAX_RETRIES} attempts: {e}")
    
    def _make_openai_call(self, prompt_text: str):
        """
        Make API call to OpenAI DALL-E.
        
        Args:
            prompt_text: The text prompt for image generation
            
        Returns:
            OpenAI API response dictionary
        """
        try:
            response = self.client.images.generate(
                model=GenerationConfig.DALLE_MODEL,
                prompt=prompt_text,
                size=GenerationConfig.OPENAI_IMAGE_SIZE,
                response_format=GenerationConfig.OPENAI_RESPONSE_FORMAT,
                n=1
            )
            
            return {
                'data': [{'url': response.data[0].url}]
            }
            
        except Exception as e:
            error_message = str(e).lower()
            
            if "authentication" in error_message or "api key" in error_message:
                raise APIAuthenticationError(f"OpenAI API authentication failed: {e}")
            elif "rate limit" in error_message or "quota" in error_message:
                raise APIRateLimitError(f"OpenAI API rate limit exceeded: {e}")
            else:
                raise ImageGenerationError(f"OpenAI API call failed: {e}")
    
    def _make_google_cloud_call(self, prompt_text: str):
        """
        Make API call to Google Cloud Vertex AI Imagen.
        
        Args:
            prompt_text: The text prompt for image generation
            
        Returns:
            Generated image response from Vertex AI
        """
        try:
            # Generate image using Vertex AI Imagen
            response = self.model.generate_images(
                prompt=prompt_text,
                number_of_images=1,
                aspect_ratio=GenerationConfig.GCP_ASPECT_RATIO,
                guidance_scale=GenerationConfig.GCP_GUIDANCE_SCALE,
                seed=GenerationConfig.GCP_SEED
            )
            
            if not response.images:
                raise ImageGenerationError("No images generated by Google Cloud")
            
            return response.images[0]
            
        except Exception as e:
            error_message = str(e).lower()
            
            if "authentication" in error_message or "permission" in error_message:
                raise APIAuthenticationError(f"Google Cloud authentication failed: {e}")
            elif "quota" in error_message or "limit" in error_message:
                raise APIRateLimitError(f"Google Cloud quota exceeded: {e}")
            else:
                raise ImageGenerationError(f"Google Cloud API call failed: {e}")
    
    def _make_freepik_call(self, prompt_text: str):
        """
        Make API call to Freepik AI using the correct API structure.
        
        Args:
            prompt_text: The text prompt for image generation
            
        Returns:
            Freepik API response dictionary with base64 images
        """
        try:
            # Prepare the request payload based on actual Freepik API
            payload = {
                "prompt": prompt_text,
                "negative_prompt": "low quality, blurry, distorted, ugly, bad anatomy",
                "guidance_scale": GenerationConfig.FREEPIK_GUIDANCE_SCALE,
                "seed": None,  # Let Freepik generate random seed
                "num_images": 1,
                "image": {
                    "size": GenerationConfig.FREEPIK_IMAGE_SIZE
                },
                "styling": {
                    "style": GenerationConfig.FREEPIK_STYLE,
                    "effects": {
                        "color": GenerationConfig.FREEPIK_COLOR_EFFECT,
                        "lightning": GenerationConfig.FREEPIK_LIGHTING,
                        "framing": GenerationConfig.FREEPIK_FRAMING
                    }
                }
            }
            
            # Make the API request
            response = requests.post(
                f"{GenerationConfig.FREEPIK_BASE_URL}/ai/text-to-image",
                headers=self.freepik_headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Check if the response contains image data
            # Based on the sample response: {"data": [{"base64": "...", "has_nsfw": false}], "meta": {...}}
            if not result.get('data') or len(result['data']) == 0:
                raise ImageGenerationError("No image data in Freepik response")
            
            # Check if first image has base64 data
            first_image = result['data'][0]
            if not first_image.get('base64'):
                raise ImageGenerationError("No base64 image data in Freepik response")
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_message = str(e).lower()
            
            if "401" in error_message or "authentication" in error_message:
                raise APIAuthenticationError(f"Freepik API authentication failed: {e}")
            elif "429" in error_message or "rate limit" in error_message:
                raise APIRateLimitError(f"Freepik API rate limit exceeded: {e}")
            else:
                raise ImageGenerationError(f"Freepik API call failed: {e}")
        except Exception as e:
            raise ImageGenerationError(f"Freepik API call failed: {e}")
    
    def _save_freepik_image(self, response: Dict[str, Any], timestamp: datetime) -> Path:
        """
        Save Freepik base64 image to local file.
        
        Args:
            response: Freepik API response containing base64 image data
            timestamp: Timestamp for filename generation
            
        Returns:
            Path to the saved image file
        """
        try:
            # Generate filename with timestamp
            filename = f"voxel_art_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
            local_path = self.images_dir / filename
            
            # Extract base64 image data from response
            image_data = response['data'][0]['base64']
            
            # Decode base64 and save to file
            image_bytes = base64.b64decode(image_data)
            
            with open(local_path, 'wb') as f:
                f.write(image_bytes)
            
            logger.info(f"Freepik image saved successfully: {local_path}")
            return local_path
            
        except Exception as e:
            raise ImageDownloadError(f"Failed to save Freepik image: {e}")
    
    def _save_google_cloud_image(self, image_response, timestamp: datetime) -> Path:
        """
        Save Google Cloud generated image to local file.
        
        Args:
            image_response: Image response from Vertex AI
            timestamp: Timestamp for filename generation
            
        Returns:
            Path to the saved image file
        """
        try:
            # Generate filename with timestamp
            filename = f"voxel_art_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
            local_path = self.images_dir / filename
            
            # Save the image directly from the response
            image_response.save(location=str(local_path))
            
            logger.info(f"Google Cloud image saved successfully: {local_path}")
            return local_path
            
        except Exception as e:
            raise ImageDownloadError(f"Failed to save Google Cloud image: {e}")
    
    def _download_image(self, image_url: str, timestamp: datetime) -> Path:
        """
        Download image from URL and save locally.
        
        Args:
            image_url: URL of the generated image
            timestamp: Timestamp for filename generation
            
        Returns:
            Path to the saved image file
            
        Raises:
            ImageDownloadError: If download fails
        """
        try:
            # Generate filename with timestamp
            filename = f"voxel_art_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
            local_path = self.images_dir / filename
            
            # Download the image
            logger.info(f"Downloading image from: {image_url}")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Save to local file
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Image downloaded successfully: {local_path}")
            return local_path
            
        except requests.exceptions.RequestException as e:
            raise ImageDownloadError(f"Failed to download image: {e}")
        except Exception as e:
            # Catch any other exception during download (including mock exceptions in tests)
            if "Network error" in str(e):
                raise ImageDownloadError(f"Failed to download image: {e}")
            elif isinstance(e, IOError):
                raise ImageDownloadError(f"Failed to save image to disk: {e}")
            else:
                raise ImageDownloadError(f"Failed to download image: {e}")
    
    def handle_api_errors(self, error: Exception) -> bool:
        """
        Handle API errors and determine if operation should be retried.
        
        Args:
            error: The exception that occurred
            
        Returns:
            True if the operation should be retried, False otherwise
        """
        if isinstance(error, APIRateLimitError):
            logger.warning("Rate limit error - will retry with backoff")
            return True
        elif isinstance(error, APIAuthenticationError):
            logger.error("Authentication error - will not retry")
            return False
        elif isinstance(error, ImageDownloadError):
            logger.warning("Download error - will retry")
            return True
        else:
            logger.error(f"Unknown error: {error}")
            return True  # Default to retry for unknown errors
    
    def cleanup_old_images(self, max_images: int = 50):
        """
        Clean up old generated images to prevent disk space issues.
        
        Args:
            max_images: Maximum number of images to keep
        """
        try:
            image_files = list(self.images_dir.glob("voxel_art_*.png"))
            if len(image_files) > max_images:
                # Sort by modification time and remove oldest
                image_files.sort(key=lambda x: x.stat().st_mtime)
                files_to_remove = image_files[:-max_images]
                
                for file_path in files_to_remove:
                    file_path.unlink()
                    logger.info(f"Removed old image: {file_path}")
                
                logger.info(f"Cleaned up {len(files_to_remove)} old images")
        
        except Exception as e:
            logger.error(f"Failed to cleanup old images: {e}")