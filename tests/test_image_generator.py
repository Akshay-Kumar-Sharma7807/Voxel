"""
Unit tests for the ImageGenerator class.
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from voxel.generation.generator import (
    ImageGenerator, 
    ImageGenerationError, 
    APIAuthenticationError, 
    APIRateLimitError,
    ImageDownloadError
)
from voxel.models import ImagePrompt, AnalysisResult, GeneratedImage


@pytest.fixture
def temp_images_dir():
    """Create a temporary directory for test images."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_analysis_result():
    """Create a sample AnalysisResult for testing."""
    return AnalysisResult(
        keywords=["sunset", "peaceful", "nature"],
        sentiment="positive",
        themes=["nature", "emotions"],
        confidence=0.8
    )


@pytest.fixture
def sample_image_prompt(sample_analysis_result):
    """Create a sample ImagePrompt for testing."""
    return ImagePrompt(
        prompt_text="A peaceful sunset over a serene lake with warm colors",
        style_modifiers=["digital painting", "warm colors"],
        source_analysis=sample_analysis_result,
        timestamp=datetime(2024, 1, 15, 14, 30, 0)
    )


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI API response."""
    return {
        "created": 1705327800,
        "data": [{"url": "https://example.com/generated_image.png"}]
    }


class TestImageGenerator:
    """Test cases for ImageGenerator class."""
    
    def test_init_with_api_key(self):
        """Test ImageGenerator initialization with provided API key."""
        generator = ImageGenerator(api_key="test-api-key")
        assert generator.api_key == "test-api-key"
    
    def test_init_with_env_api_key(self):
        """Test ImageGenerator initialization with environment variable API key."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'env-api-key'}, clear=False):
            with patch('voxel.config.SystemConfig.OPENAI_API_KEY', 'env-api-key'):
                generator = ImageGenerator()
                assert generator.api_key == "env-api-key"
    
    def test_init_without_api_key(self):
        """Test ImageGenerator initialization fails without API key."""
        with patch('voxel.config.SystemConfig.OPENAI_API_KEY', None):
            with pytest.raises(APIAuthenticationError, match="OpenAI API key not found"):
                ImageGenerator()
    
    @patch('voxel.generation.generator.SystemConfig.IMAGES_DIR')
    def test_init_creates_images_directory(self, mock_images_dir, temp_images_dir):
        """Test that ImageGenerator creates images directory on initialization."""
        mock_images_dir.return_value = temp_images_dir / "test_images"
        mock_images_dir.mkdir = Mock()
        
        generator = ImageGenerator(api_key="test-key")
        mock_images_dir.mkdir.assert_called_once_with(exist_ok=True)
    
    @patch('voxel.generation.generator.requests.get')
    @patch('voxel.generation.generator.SystemConfig.IMAGES_DIR')
    def test_generate_image_success(self, mock_images_dir, mock_requests_get, 
                                  temp_images_dir, sample_image_prompt, mock_openai_response):
        """Test successful image generation."""
        # Setup mocks
        mock_images_dir.return_value = temp_images_dir
        mock_requests_get.return_value.content = b"fake_image_data"
        mock_requests_get.return_value.raise_for_status = Mock()
        
        generator = ImageGenerator(api_key="test-key")
        generator.images_dir = temp_images_dir
        
        with patch('voxel.generation.generator.openai.Image.create', return_value=mock_openai_response):
            result = generator.generate_image(sample_image_prompt)
        
        # Verify result
        assert isinstance(result, GeneratedImage)
        assert result.url == "https://example.com/generated_image.png"
        assert result.prompt == sample_image_prompt
        assert result.local_path.endswith(".png")
        assert Path(result.local_path).exists()
    
    @patch('voxel.generation.generator.openai.Image.create')
    def test_make_api_call_success(self, mock_create, sample_image_prompt, mock_openai_response):
        """Test successful API call."""
        mock_create.return_value = mock_openai_response
        generator = ImageGenerator(api_key="test-key")
        
        result = generator._make_api_call(sample_image_prompt.prompt_text)
        
        assert result == mock_openai_response
        mock_create.assert_called_once_with(
            model="dall-e-3",
            prompt=sample_image_prompt.prompt_text,
            size="1024x1024",
            response_format="url",
            n=1
        )
    
    @patch('voxel.generation.generator.openai.Image.create')
    def test_make_api_call_authentication_error(self, mock_create, sample_image_prompt):
        """Test API call with authentication error."""
        mock_create.side_effect = Exception("Invalid API key provided")
        generator = ImageGenerator(api_key="test-key")
        
        with pytest.raises(APIAuthenticationError, match="API authentication failed"):
            generator._make_api_call(sample_image_prompt.prompt_text)
    
    @patch('voxel.generation.generator.openai.Image.create')
    def test_make_api_call_rate_limit_error(self, mock_create, sample_image_prompt):
        """Test API call with rate limit error."""
        mock_create.side_effect = Exception("Rate limit exceeded")
        generator = ImageGenerator(api_key="test-key")
        
        with pytest.raises(APIRateLimitError, match="API rate limit exceeded"):
            generator._make_api_call(sample_image_prompt.prompt_text)
    
    @patch('voxel.generation.generator.openai.Image.create')
    def test_make_api_call_generic_error(self, mock_create, sample_image_prompt):
        """Test API call with generic error."""
        mock_create.side_effect = Exception("Some other error")
        generator = ImageGenerator(api_key="test-key")
        
        with pytest.raises(ImageGenerationError, match="API call failed"):
            generator._make_api_call(sample_image_prompt.prompt_text)
    
    @patch('voxel.generation.generator.requests.get')
    def test_download_image_success(self, mock_requests_get, temp_images_dir):
        """Test successful image download."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = b"fake_image_data"
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response
        
        generator = ImageGenerator(api_key="test-key")
        generator.images_dir = temp_images_dir
        
        timestamp = datetime(2024, 1, 15, 14, 30, 0)
        result_path = generator._download_image("https://example.com/image.png", timestamp)
        
        # Verify download
        assert result_path.exists()
        assert result_path.name == "voxel_art_20240115_143000.png"
        assert result_path.read_bytes() == b"fake_image_data"
        mock_requests_get.assert_called_once_with("https://example.com/image.png", timeout=30)
    
    @patch('voxel.generation.generator.requests.get')
    def test_download_image_request_error(self, mock_requests_get, temp_images_dir):
        """Test image download with request error."""
        mock_requests_get.side_effect = Exception("Network error")
        
        generator = ImageGenerator(api_key="test-key")
        generator.images_dir = temp_images_dir
        
        timestamp = datetime(2024, 1, 15, 14, 30, 0)
        with pytest.raises(ImageDownloadError, match="Failed to download image"):
            generator._download_image("https://example.com/image.png", timestamp)
    
    @patch('voxel.generation.generator.requests.get')
    @patch('builtins.open', side_effect=IOError("Disk full"))
    def test_download_image_io_error(self, mock_open, mock_requests_get, temp_images_dir):
        """Test image download with IO error."""
        mock_response = Mock()
        mock_response.content = b"fake_image_data"
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response
        
        generator = ImageGenerator(api_key="test-key")
        generator.images_dir = temp_images_dir
        
        timestamp = datetime(2024, 1, 15, 14, 30, 0)
        with pytest.raises(ImageDownloadError, match="Failed to save image to disk"):
            generator._download_image("https://example.com/image.png", timestamp)
    
    @patch('voxel.generation.generator.time.sleep')
    def test_generate_image_with_retries(self, mock_sleep, sample_image_prompt, 
                                       mock_openai_response, temp_images_dir):
        """Test image generation with retry logic."""
        generator = ImageGenerator(api_key="test-key")
        generator.images_dir = temp_images_dir
        
        # Mock API to fail twice then succeed
        api_calls = [
            APIRateLimitError("Rate limit exceeded"),
            APIRateLimitError("Rate limit exceeded"),
            mock_openai_response
        ]
        
        with patch.object(generator, '_make_api_call', side_effect=api_calls):
            with patch.object(generator, '_download_image', return_value=Path("test.png")):
                result = generator.generate_image(sample_image_prompt)
        
        assert isinstance(result, GeneratedImage)
        assert mock_sleep.call_count == 2  # Two retries with sleep
    
    def test_generate_image_max_retries_exceeded(self, sample_image_prompt):
        """Test image generation fails after max retries."""
        generator = ImageGenerator(api_key="test-key")
        
        with patch.object(generator, '_make_api_call', 
                         side_effect=APIRateLimitError("Rate limit exceeded")):
            with pytest.raises(ImageGenerationError, match="Failed to generate image after 3 attempts"):
                generator.generate_image(sample_image_prompt)
    
    def test_handle_api_errors(self):
        """Test API error handling logic."""
        generator = ImageGenerator(api_key="test-key")
        
        # Test different error types
        assert generator.handle_api_errors(APIRateLimitError("Rate limit")) == True
        assert generator.handle_api_errors(APIAuthenticationError("Auth failed")) == False
        assert generator.handle_api_errors(ImageDownloadError("Download failed")) == True
        assert generator.handle_api_errors(Exception("Unknown error")) == True
    
    def test_cleanup_old_images(self, temp_images_dir):
        """Test cleanup of old generated images."""
        generator = ImageGenerator(api_key="test-key")
        generator.images_dir = temp_images_dir
        
        # Create test image files
        for i in range(5):
            test_file = temp_images_dir / f"voxel_art_202401{i:02d}_120000.png"
            test_file.write_text("test")
        
        # Cleanup keeping only 3 images
        generator.cleanup_old_images(max_images=3)
        
        remaining_files = list(temp_images_dir.glob("voxel_art_*.png"))
        assert len(remaining_files) == 3
    
    def test_cleanup_old_images_error_handling(self, temp_images_dir):
        """Test cleanup handles errors gracefully."""
        generator = ImageGenerator(api_key="test-key")
        generator.images_dir = temp_images_dir
        
        # Create a file and make it unremovable (simulate permission error)
        test_file = temp_images_dir / "voxel_art_20240101_120000.png"
        test_file.write_text("test")
        
        with patch.object(Path, 'unlink', side_effect=PermissionError("Permission denied")):
            # Should not raise exception
            generator.cleanup_old_images(max_images=0)


class TestImageGeneratorIntegration:
    """Integration tests for ImageGenerator."""
    
    @patch('voxel.generation.generator.requests.get')
    def test_full_workflow_mock(self, mock_requests_get, sample_image_prompt, 
                               mock_openai_response, temp_images_dir):
        """Test complete image generation workflow with mocked external calls."""
        # Setup mocks
        mock_response = Mock()
        mock_response.content = b"fake_image_data"
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response
        
        generator = ImageGenerator(api_key="test-key")
        generator.images_dir = temp_images_dir
        
        with patch('voxel.generation.generator.openai.Image.create', return_value=mock_openai_response):
            result = generator.generate_image(sample_image_prompt)
        
        # Verify complete workflow
        assert isinstance(result, GeneratedImage)
        assert result.url == "https://example.com/generated_image.png"
        assert result.prompt == sample_image_prompt
        assert Path(result.local_path).exists()
        assert Path(result.local_path).read_bytes() == b"fake_image_data"
        
        # Verify API was called correctly
        mock_requests_get.assert_called_once()