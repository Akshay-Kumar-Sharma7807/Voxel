"""
Display controller for managing fullscreen image display on Raspberry Pi.
"""

import logging
import subprocess
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import pygame

from ..config import DisplayConfig, SystemConfig
from ..models import GeneratedImage


class DisplayError(Exception):
    """Custom exception for display-related errors."""
    pass


class DisplayController:
    """
    Manages fullscreen image display on Raspberry Pi with FBI and Pygame fallback.
    
    The controller handles image preprocessing, display method selection,
    and error recovery for robust operation.
    """
    
    def __init__(self):
        """Initialize the display controller."""
        self.logger = logging.getLogger(__name__)
        self.current_image_path: Optional[str] = None
        self.screen_resolution: Optional[Tuple[int, int]] = None
        self.pygame_initialized = False
        
        # Ensure image cache directory exists
        SystemConfig.IMAGES_DIR.mkdir(exist_ok=True)
        
        # Detect screen resolution
        self._detect_screen_resolution()
        
    def _detect_screen_resolution(self) -> None:
        """Detect the current screen resolution."""
        try:
            # Try to get resolution from framebuffer
            result = subprocess.run(
                ["fbset", "-s"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse fbset output for resolution
                for line in result.stdout.split('\n'):
                    if 'geometry' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            width = int(parts[1])
                            height = int(parts[2])
                            self.screen_resolution = (width, height)
                            self.logger.info(f"Detected screen resolution: {width}x{height}")
                            return
            
            # Fallback: try xrandr if available
            result = subprocess.run(
                ["xrandr", "--current"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if '*' in line and 'x' in line:
                        # Parse line like "   1920x1080     60.00*+"
                        resolution_part = line.split()[0]
                        if 'x' in resolution_part:
                            width, height = map(int, resolution_part.split('x'))
                            self.screen_resolution = (width, height)
                            self.logger.info(f"Detected screen resolution: {width}x{height}")
                            return
                            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError) as e:
            self.logger.warning(f"Could not detect screen resolution: {e}")
        
        # Default fallback resolution
        self.screen_resolution = (1920, 1080)
        self.logger.info(f"Using default screen resolution: {self.screen_resolution[0]}x{self.screen_resolution[1]}")
    
    def _preprocess_image(self, image_path: str) -> str:
        """
        Preprocess image to fit screen resolution.
        
        Args:
            image_path: Path to the original image
            
        Returns:
            Path to the preprocessed image
            
        Raises:
            DisplayError: If image preprocessing fails
        """
        try:
            # Open the image
            with Image.open(image_path) as img:
                original_size = img.size
                self.logger.debug(f"Original image size: {original_size}")
                
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate target size maintaining aspect ratio
                target_width, target_height = self.screen_resolution
                img_width, img_height = img.size
                
                # Calculate scaling factor to fit screen while maintaining aspect ratio
                scale_width = target_width / img_width
                scale_height = target_height / img_height
                scale_factor = min(scale_width, scale_height)
                
                # Calculate new dimensions
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)
                
                # Resize image
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Create a black background of screen size
                background = Image.new('RGB', (target_width, target_height), (0, 0, 0))
                
                # Center the resized image on the background
                x_offset = (target_width - new_width) // 2
                y_offset = (target_height - new_height) // 2
                background.paste(img_resized, (x_offset, y_offset))
                
                # Save preprocessed image
                preprocessed_path = str(SystemConfig.IMAGES_DIR / f"display_{Path(image_path).name}")
                background.save(preprocessed_path, 'JPEG', quality=95)
                
                self.logger.debug(f"Preprocessed image saved to: {preprocessed_path}")
                return preprocessed_path
                
        except Exception as e:
            raise DisplayError(f"Failed to preprocess image {image_path}: {e}")
    
    def _display_with_fbi(self, image_path: str) -> bool:
        """
        Display image using FBI framebuffer imageviewer.
        
        Args:
            image_path: Path to the image to display
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if FBI is available
            if not shutil.which("fbi"):
                self.logger.warning("FBI command not found")
                return False
            
            # Clear any existing FBI processes
            subprocess.run(["pkill", "-f", "fbi"], capture_output=True)
            
            # Display image with FBI
            cmd = [
                "fbi",
                "-T", "1",  # Use framebuffer 1 (or adjust as needed)
                "-d", "/dev/fb0",  # Framebuffer device
                "-noverbose",
                "-a",  # Auto-zoom to fit screen
                image_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully displayed image with FBI: {image_path}")
                return True
            else:
                self.logger.warning(f"FBI failed with return code {result.returncode}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.warning("FBI command timed out")
            return False
        except Exception as e:
            self.logger.warning(f"FBI display failed: {e}")
            return False
    
    def _display_with_pygame(self, image_path: str) -> bool:
        """
        Display image using Pygame as fallback method.
        
        Args:
            image_path: Path to the image to display
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize Pygame if not already done
            if not self.pygame_initialized:
                pygame.init()
                pygame.display.init()
                self.pygame_initialized = True
            
            # Load image
            image = pygame.image.load(image_path)
            
            # Set up display
            if DisplayConfig.FULLSCREEN:
                screen = pygame.display.set_mode(self.screen_resolution, pygame.FULLSCREEN)
            else:
                screen = pygame.display.set_mode(self.screen_resolution)
            
            pygame.display.set_caption("Voxel Ambient Art")
            
            # Fill screen with black
            screen.fill((0, 0, 0))
            
            # Scale and center image
            image_rect = image.get_rect()
            screen_rect = screen.get_rect()
            
            # Scale image to fit screen while maintaining aspect ratio
            scale_x = screen_rect.width / image_rect.width
            scale_y = screen_rect.height / image_rect.height
            scale = min(scale_x, scale_y)
            
            new_width = int(image_rect.width * scale)
            new_height = int(image_rect.height * scale)
            
            scaled_image = pygame.transform.scale(image, (new_width, new_height))
            scaled_rect = scaled_image.get_rect(center=screen_rect.center)
            
            # Blit image to screen
            screen.blit(scaled_image, scaled_rect)
            pygame.display.flip()
            
            self.logger.info(f"Successfully displayed image with Pygame: {image_path}")
            return True
            
        except Exception as e:
            self.logger.warning(f"Pygame display failed: {e}")
            return False
    
    def display_image(self, generated_image: GeneratedImage) -> bool:
        """
        Display a generated image fullscreen.
        
        Args:
            generated_image: The GeneratedImage object to display
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            DisplayError: If both display methods fail
        """
        try:
            image_path = generated_image.local_path
            
            # Validate image file exists
            if not os.path.exists(image_path):
                raise DisplayError(f"Image file not found: {image_path}")
            
            # Preprocess image for optimal display
            preprocessed_path = self._preprocess_image(image_path)
            
            # Try primary display method (FBI)
            if DisplayConfig.DISPLAY_METHOD_PRIMARY == "fbi":
                if self._display_with_fbi(preprocessed_path):
                    self.current_image_path = preprocessed_path
                    return True
                
                self.logger.info("FBI display failed, trying Pygame fallback")
            
            # Try fallback method (Pygame)
            if self._display_with_pygame(preprocessed_path):
                self.current_image_path = preprocessed_path
                return True
            
            # Both methods failed
            raise DisplayError("Both FBI and Pygame display methods failed")
            
        except DisplayError:
            raise
        except Exception as e:
            raise DisplayError(f"Failed to display image: {e}")
    
    def clear_display(self) -> bool:
        """
        Clear the current display.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Kill any FBI processes
            subprocess.run(["pkill", "-f", "fbi"], capture_output=True)
            
            # Clear Pygame display if initialized
            if self.pygame_initialized:
                try:
                    screen = pygame.display.get_surface()
                    if screen:
                        screen.fill((0, 0, 0))
                        pygame.display.flip()
                except:
                    pass
            
            self.current_image_path = None
            self.logger.info("Display cleared")
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to clear display: {e}")
            return False
    
    def handle_display_errors(self, error: Exception) -> bool:
        """
        Handle display errors and attempt recovery.
        
        Args:
            error: The error that occurred
            
        Returns:
            True if recovery was successful, False otherwise
        """
        self.logger.error(f"Display error occurred: {error}")
        
        try:
            # Clear any stuck processes
            self.clear_display()
            
            # Reset Pygame if it was initialized
            if self.pygame_initialized:
                try:
                    pygame.quit()
                    self.pygame_initialized = False
                except:
                    pass
            
            # Re-detect screen resolution
            self._detect_screen_resolution()
            
            self.logger.info("Display error recovery completed")
            return True
            
        except Exception as recovery_error:
            self.logger.error(f"Display error recovery failed: {recovery_error}")
            return False
    
    def cleanup(self) -> None:
        """Clean up display resources."""
        try:
            self.clear_display()
            
            if self.pygame_initialized:
                pygame.quit()
                self.pygame_initialized = False
            
            # Clean up preprocessed images
            try:
                for file_path in SystemConfig.IMAGES_DIR.glob("display_*"):
                    file_path.unlink()
            except:
                pass
                
            self.logger.info("Display controller cleanup completed")
            
        except Exception as e:
            self.logger.warning(f"Display cleanup failed: {e}")