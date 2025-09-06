"""
Unit tests for the DisplayController class.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import tempfile
import os
import shutil
from pathlib import Path
from datetime import datetime
from PIL import Image
import subprocess

from voxel.display.controller import DisplayController, DisplayError
from voxel.models import GeneratedImage, ImagePrompt, AnalysisResult


class TestDisplayController(unittest.TestCase):
    """Test cases for DisplayController class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_image_path = os.path.join(self.temp_dir, "test_image.jpg")
        
        # Create a test image
        test_image = Image.new('RGB', (800, 600), color='red')
        test_image.save(self.test_image_path, 'JPEG')
        
        # Create test GeneratedImage object
        analysis_result = AnalysisResult(
            keywords=["test", "image"],
            sentiment="positive",
            themes=["art"],
            confidence=0.8
        )
        
        image_prompt = ImagePrompt(
            prompt_text="A test image",
            style_modifiers=["digital art"],
            source_analysis=analysis_result,
            timestamp=datetime.now()
        )
        
        self.test_generated_image = GeneratedImage(
            url="http://example.com/image.jpg",
            local_path=self.test_image_path,
            prompt=image_prompt,
            generation_time=datetime.now(),
            api_response={}
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp files and directories
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
    
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    def test_init_with_fbset_resolution_detection(self, mock_images_dir, mock_subprocess):
        """Test initialization with fbset resolution detection."""
        # Mock fbset output
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "geometry 1920 1080 1920 1080 32"
        mock_subprocess.return_value = mock_result
        
        mock_images_dir.mkdir = Mock()
        
        controller = DisplayController()
        
        self.assertEqual(controller.screen_resolution, (1920, 1080))
        self.assertIsNone(controller.current_image_path)
        self.assertFalse(controller.pygame_initialized)
    
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    def test_init_with_xrandr_fallback(self, mock_images_dir, mock_subprocess):
        """Test initialization with xrandr fallback resolution detection."""
        # Mock fbset failure and xrandr success
        def mock_subprocess_side_effect(*args, **kwargs):
            if 'fbset' in args[0]:
                result = Mock()
                result.returncode = 1
                return result
            elif 'xrandr' in args[0]:
                result = Mock()
                result.returncode = 0
                result.stdout = "   1920x1080     60.00*+   59.93"
                return result
        
        mock_subprocess.side_effect = mock_subprocess_side_effect
        mock_images_dir.mkdir = Mock()
        
        controller = DisplayController()
        
        self.assertEqual(controller.screen_resolution, (1920, 1080))
    
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    def test_init_with_default_resolution(self, mock_images_dir, mock_subprocess):
        """Test initialization with default resolution fallback."""
        # Mock both fbset and xrandr failure
        mock_result = Mock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result
        mock_images_dir.mkdir = Mock()
        
        controller = DisplayController()
        
        self.assertEqual(controller.screen_resolution, (1920, 1080))
    
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    def test_preprocess_image_success(self, mock_images_dir, mock_subprocess):
        """Test successful image preprocessing."""
        mock_images_dir.__truediv__ = Mock(return_value=Path(self.temp_dir) / "display_test_image.jpg")
        mock_images_dir.mkdir = Mock()
        
        # Mock subprocess for resolution detection
        mock_subprocess.return_value.returncode = 1  # Fail both fbset and xrandr
        
        controller = DisplayController()
        controller.screen_resolution = (1920, 1080)
        
        preprocessed_path = controller._preprocess_image(self.test_image_path)
        
        self.assertTrue(os.path.exists(preprocessed_path))
        
        # Verify preprocessed image dimensions
        with Image.open(preprocessed_path) as img:
            self.assertEqual(img.size, (1920, 1080))
    
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    def test_preprocess_image_nonexistent_file(self, mock_images_dir, mock_subprocess):
        """Test preprocessing with nonexistent image file."""
        mock_images_dir.mkdir = Mock()
        mock_subprocess.return_value.returncode = 1  # Fail both fbset and xrandr
        
        controller = DisplayController()
        
        with self.assertRaises(DisplayError):
            controller._preprocess_image("/nonexistent/image.jpg")
    
    @patch('voxel.display.controller.shutil.which')
    @patch('voxel.display.controller.subprocess.run')
    def test_display_with_fbi_success(self, mock_subprocess, mock_which):
        """Test successful FBI display."""
        mock_which.return_value = "/usr/bin/fbi"
        mock_subprocess.return_value.returncode = 0
        
        controller = DisplayController()
        
        result = controller._display_with_fbi(self.test_image_path)
        
        self.assertTrue(result)
        # Verify FBI was called with correct arguments
        mock_subprocess.assert_called()
    
    @patch('voxel.display.controller.shutil.which')
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    def test_display_with_fbi_not_available(self, mock_images_dir, mock_subprocess, mock_which):
        """Test FBI display when FBI is not available."""
        mock_which.return_value = None
        
        # Mock subprocess for resolution detection
        mock_subprocess.return_value.returncode = 1  # Fail both fbset and xrandr
        mock_images_dir.mkdir = Mock()
        
        controller = DisplayController()
        
        result = controller._display_with_fbi(self.test_image_path)
        
        self.assertFalse(result)
    
    @patch('voxel.display.controller.shutil.which')
    @patch('voxel.display.controller.subprocess.run')
    def test_display_with_fbi_failure(self, mock_subprocess, mock_which):
        """Test FBI display failure."""
        mock_which.return_value = "/usr/bin/fbi"
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "Error message"
        
        controller = DisplayController()
        
        result = controller._display_with_fbi(self.test_image_path)
        
        self.assertFalse(result)
    
    @patch('voxel.display.controller.pygame')
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    def test_display_with_pygame_success(self, mock_images_dir, mock_subprocess, mock_pygame):
        """Test successful Pygame display."""
        # Mock pygame components
        mock_pygame.init = Mock()
        mock_pygame.display.init = Mock()
        mock_pygame.image.load = Mock()
        mock_pygame.display.set_mode = Mock()
        mock_pygame.display.set_caption = Mock()
        mock_pygame.display.flip = Mock()
        mock_pygame.transform.scale = Mock()
        
        # Mock image and surface objects
        mock_image = Mock()
        mock_image.get_rect.return_value = Mock(width=800, height=600)
        mock_pygame.image.load.return_value = mock_image
        
        mock_screen = Mock()
        mock_screen.get_rect.return_value = Mock(width=1920, height=1080, center=(960, 540))
        mock_screen.fill = Mock()
        mock_screen.blit = Mock()
        mock_pygame.display.set_mode.return_value = mock_screen
        
        mock_scaled_image = Mock()
        mock_scaled_image.get_rect.return_value = Mock()
        mock_pygame.transform.scale.return_value = mock_scaled_image
        
        # Mock subprocess for resolution detection
        mock_subprocess.return_value.returncode = 1  # Fail both fbset and xrandr
        mock_images_dir.mkdir = Mock()
        
        controller = DisplayController()
        controller.screen_resolution = (1920, 1080)
        
        result = controller._display_with_pygame(self.test_image_path)
        
        self.assertTrue(result)
        self.assertTrue(controller.pygame_initialized)
    
    @patch('voxel.display.controller.pygame')
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    def test_display_with_pygame_failure(self, mock_images_dir, mock_subprocess, mock_pygame):
        """Test Pygame display failure."""
        mock_pygame.init.side_effect = Exception("Pygame error")
        
        # Mock subprocess for resolution detection
        mock_subprocess.return_value.returncode = 1  # Fail both fbset and xrandr
        mock_images_dir.mkdir = Mock()
        
        controller = DisplayController()
        
        result = controller._display_with_pygame(self.test_image_path)
        
        self.assertFalse(result)
    
    @patch.object(DisplayController, '_preprocess_image')
    @patch.object(DisplayController, '_display_with_fbi')
    @patch.object(DisplayController, '_display_with_pygame')
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    def test_display_image_success_with_fbi(self, mock_images_dir, mock_subprocess, mock_pygame_display, mock_fbi_display, mock_preprocess):
        """Test successful image display with FBI."""
        mock_preprocess.return_value = "/path/to/preprocessed.jpg"
        mock_fbi_display.return_value = True
        
        # Mock subprocess for resolution detection
        mock_subprocess.return_value.returncode = 1  # Fail both fbset and xrandr
        mock_images_dir.mkdir = Mock()
        
        controller = DisplayController()
        
        result = controller.display_image(self.test_generated_image)
        
        self.assertTrue(result)
        self.assertEqual(controller.current_image_path, "/path/to/preprocessed.jpg")
        mock_fbi_display.assert_called_once()
        mock_pygame_display.assert_not_called()
    
    @patch.object(DisplayController, '_preprocess_image')
    @patch.object(DisplayController, '_display_with_fbi')
    @patch.object(DisplayController, '_display_with_pygame')
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    def test_display_image_fallback_to_pygame(self, mock_images_dir, mock_subprocess, mock_pygame_display, mock_fbi_display, mock_preprocess):
        """Test image display fallback to Pygame when FBI fails."""
        mock_preprocess.return_value = "/path/to/preprocessed.jpg"
        mock_fbi_display.return_value = False
        mock_pygame_display.return_value = True
        
        # Mock subprocess for resolution detection
        mock_subprocess.return_value.returncode = 1  # Fail both fbset and xrandr
        mock_images_dir.mkdir = Mock()
        
        controller = DisplayController()
        
        result = controller.display_image(self.test_generated_image)
        
        self.assertTrue(result)
        self.assertEqual(controller.current_image_path, "/path/to/preprocessed.jpg")
        mock_fbi_display.assert_called_once()
        mock_pygame_display.assert_called_once()
    
    @patch.object(DisplayController, '_preprocess_image')
    @patch.object(DisplayController, '_display_with_fbi')
    @patch.object(DisplayController, '_display_with_pygame')
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    def test_display_image_both_methods_fail(self, mock_images_dir, mock_subprocess, mock_pygame_display, mock_fbi_display, mock_preprocess):
        """Test image display when both methods fail."""
        mock_preprocess.return_value = "/path/to/preprocessed.jpg"
        mock_fbi_display.return_value = False
        mock_pygame_display.return_value = False
        
        # Mock subprocess for resolution detection
        mock_subprocess.return_value.returncode = 1  # Fail both fbset and xrandr
        mock_images_dir.mkdir = Mock()
        
        controller = DisplayController()
        
        with self.assertRaises(DisplayError):
            controller.display_image(self.test_generated_image)
    
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    def test_display_image_nonexistent_file(self, mock_images_dir, mock_subprocess):
        """Test display image with nonexistent file."""
        # Create GeneratedImage with nonexistent path
        bad_generated_image = GeneratedImage(
            url="http://example.com/image.jpg",
            local_path="/nonexistent/image.jpg",
            prompt=self.test_generated_image.prompt,
            generation_time=datetime.now(),
            api_response={}
        )
        
        # Mock subprocess for resolution detection
        mock_subprocess.return_value.returncode = 1  # Fail both fbset and xrandr
        mock_images_dir.mkdir = Mock()
        
        controller = DisplayController()
        
        with self.assertRaises(DisplayError):
            controller.display_image(bad_generated_image)
    
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.pygame')
    def test_clear_display_success(self, mock_pygame, mock_subprocess):
        """Test successful display clearing."""
        # Mock pygame components
        mock_screen = Mock()
        mock_screen.fill = Mock()
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_pygame.display.flip = Mock()
        
        controller = DisplayController()
        controller.pygame_initialized = True
        controller.current_image_path = "/some/path.jpg"
        
        result = controller.clear_display()
        
        self.assertTrue(result)
        self.assertIsNone(controller.current_image_path)
        mock_subprocess.assert_called_with(["pkill", "-f", "fbi"], capture_output=True)
    
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    def test_clear_display_failure(self, mock_images_dir, mock_subprocess):
        """Test display clearing failure."""
        # Mock initialization subprocess calls
        def mock_subprocess_side_effect(*args, **kwargs):
            if args[0] == ["pkill", "-f", "fbi"]:
                raise Exception("Process error")
            else:
                # For fbset/xrandr calls during initialization
                result = Mock()
                result.returncode = 1
                return result
        
        mock_subprocess.side_effect = mock_subprocess_side_effect
        mock_images_dir.mkdir = Mock()
        
        controller = DisplayController()
        
        result = controller.clear_display()
        
        self.assertFalse(result)
    
    @patch.object(DisplayController, 'clear_display')
    @patch.object(DisplayController, '_detect_screen_resolution')
    @patch('voxel.display.controller.pygame')
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    def test_handle_display_errors_success(self, mock_images_dir, mock_subprocess, mock_pygame, mock_detect_resolution, mock_clear_display):
        """Test successful display error handling."""
        mock_clear_display.return_value = True
        mock_pygame.quit = Mock()
        
        # Mock subprocess for resolution detection
        mock_subprocess.return_value.returncode = 1  # Fail both fbset and xrandr
        mock_images_dir.mkdir = Mock()
        
        controller = DisplayController()
        controller.pygame_initialized = True
        
        error = DisplayError("Test error")
        result = controller.handle_display_errors(error)
        
        self.assertTrue(result)
        self.assertFalse(controller.pygame_initialized)
        mock_clear_display.assert_called_once()
        # _detect_screen_resolution is called twice: once during init and once during error recovery
        self.assertEqual(mock_detect_resolution.call_count, 2)
    
    @patch.object(DisplayController, 'clear_display')
    @patch('voxel.display.controller.subprocess.run')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    def test_handle_display_errors_failure(self, mock_images_dir, mock_subprocess, mock_clear_display):
        """Test display error handling failure."""
        mock_clear_display.side_effect = Exception("Recovery error")
        
        # Mock subprocess for resolution detection
        mock_subprocess.return_value.returncode = 1  # Fail both fbset and xrandr
        mock_images_dir.mkdir = Mock()
        
        controller = DisplayController()
        
        error = DisplayError("Test error")
        result = controller.handle_display_errors(error)
        
        self.assertFalse(result)
    
    @patch.object(DisplayController, 'clear_display')
    @patch('voxel.display.controller.pygame')
    @patch('voxel.display.controller.SystemConfig.IMAGES_DIR')
    @patch('voxel.display.controller.subprocess.run')
    def test_cleanup_success(self, mock_subprocess, mock_images_dir, mock_pygame, mock_clear_display):
        """Test successful cleanup."""
        mock_clear_display.return_value = True
        mock_pygame.quit = Mock()
        
        # Mock subprocess for resolution detection
        mock_subprocess.return_value.returncode = 1  # Fail both fbset and xrandr
        mock_images_dir.mkdir = Mock()
        
        # Mock glob for cleanup
        mock_file = Mock()
        mock_file.unlink = Mock()
        mock_images_dir.glob.return_value = [mock_file]
        
        controller = DisplayController()
        controller.pygame_initialized = True
        
        controller.cleanup()
        
        self.assertFalse(controller.pygame_initialized)
        mock_clear_display.assert_called_once()
        mock_pygame.quit.assert_called_once()
        mock_file.unlink.assert_called_once()


if __name__ == '__main__':
    unittest.main()