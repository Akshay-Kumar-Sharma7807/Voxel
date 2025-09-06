#!/usr/bin/env python3
"""
Example script demonstrating DisplayController functionality.
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from voxel.display.controller import DisplayController, DisplayError
from voxel.models import GeneratedImage, ImagePrompt, AnalysisResult


def create_test_image(image_path: str, color: str = 'blue', size: tuple = (800, 600)) -> None:
    """Create a test image for demonstration."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create image with solid color background
        img = Image.new('RGB', size, color)
        draw = ImageDraw.Draw(img)
        
        # Add some text
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
        
        text = f"Test Image - {color.title()}\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Calculate text position (center)
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width, text_height = 200, 50  # Approximate
        
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        # Draw text with contrasting color
        text_color = 'white' if color in ['blue', 'red', 'black'] else 'black'
        draw.text((x, y), text, fill=text_color, font=font)
        
        # Save image
        img.save(image_path, 'JPEG', quality=95)
        print(f"Created test image: {image_path}")
        
    except ImportError:
        print("PIL not available, creating simple test file")
        with open(image_path, 'w') as f:
            f.write("Test image placeholder")


def create_test_generated_image(image_path: str) -> GeneratedImage:
    """Create a test GeneratedImage object."""
    analysis_result = AnalysisResult(
        keywords=["test", "display", "example"],
        sentiment="positive",
        themes=["technology", "art"],
        confidence=0.9
    )
    
    image_prompt = ImagePrompt(
        prompt_text="A beautiful test image for display controller demonstration",
        style_modifiers=["digital art", "vibrant colors"],
        source_analysis=analysis_result,
        timestamp=datetime.now()
    )
    
    return GeneratedImage(
        url="http://example.com/test_image.jpg",
        local_path=image_path,
        prompt=image_prompt,
        generation_time=datetime.now(),
        api_response={"status": "success"}
    )


def test_display_controller():
    """Test the DisplayController functionality."""
    print("=== DisplayController Test ===")
    
    # Create test images directory
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)
    
    try:
        # Initialize display controller
        print("\n1. Initializing DisplayController...")
        controller = DisplayController()
        print(f"   Screen resolution detected: {controller.screen_resolution}")
        
        # Create test images
        print("\n2. Creating test images...")
        test_images = []
        colors = ['blue', 'red', 'green']
        
        for i, color in enumerate(colors):
            image_path = test_dir / f"test_image_{color}.jpg"
            create_test_image(str(image_path), color)
            generated_image = create_test_generated_image(str(image_path))
            test_images.append(generated_image)
        
        # Test image preprocessing
        print("\n3. Testing image preprocessing...")
        try:
            preprocessed_path = controller._preprocess_image(str(test_images[0].local_path))
            print(f"   Preprocessed image saved to: {preprocessed_path}")
        except Exception as e:
            print(f"   Preprocessing failed: {e}")
        
        # Test display methods
        print("\n4. Testing display methods...")
        
        # Test FBI display (will likely fail on non-Raspberry Pi systems)
        print("   Testing FBI display method...")
        fbi_result = controller._display_with_fbi(str(test_images[0].local_path))
        print(f"   FBI display result: {fbi_result}")
        
        # Test Pygame display
        print("   Testing Pygame display method...")
        try:
            pygame_result = controller._display_with_pygame(str(test_images[0].local_path))
            print(f"   Pygame display result: {pygame_result}")
            
            if pygame_result:
                print("   Image displayed with Pygame. Press Enter to continue...")
                input()
        except Exception as e:
            print(f"   Pygame display failed: {e}")
        
        # Test full display_image method
        print("\n5. Testing full display_image method...")
        for i, generated_image in enumerate(test_images):
            try:
                print(f"   Displaying image {i+1}: {Path(generated_image.local_path).name}")
                result = controller.display_image(generated_image)
                print(f"   Display result: {result}")
                
                if result:
                    print(f"   Image displayed successfully. Waiting 3 seconds...")
                    time.sleep(3)
                
            except DisplayError as e:
                print(f"   Display error: {e}")
            except Exception as e:
                print(f"   Unexpected error: {e}")
        
        # Test clear display
        print("\n6. Testing clear display...")
        clear_result = controller.clear_display()
        print(f"   Clear display result: {clear_result}")
        
        # Test error handling
        print("\n7. Testing error handling...")
        try:
            # Try to display non-existent image
            bad_image = create_test_generated_image("/nonexistent/image.jpg")
            controller.display_image(bad_image)
        except DisplayError as e:
            print(f"   Expected error caught: {e}")
        
        # Test error recovery
        print("   Testing error recovery...")
        test_error = DisplayError("Test error for recovery")
        recovery_result = controller.handle_display_errors(test_error)
        print(f"   Error recovery result: {recovery_result}")
        
        print("\n8. Testing cleanup...")
        controller.cleanup()
        print("   Cleanup completed")
        
        print("\n=== DisplayController Test Completed ===")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test images
        try:
            for image_file in test_dir.glob("*.jpg"):
                image_file.unlink()
            test_dir.rmdir()
            print("Test images cleaned up")
        except:
            pass


def test_display_methods_availability():
    """Test which display methods are available on the current system."""
    print("=== Display Methods Availability Test ===")
    
    import shutil
    import subprocess
    
    # Check FBI availability
    fbi_available = shutil.which("fbi") is not None
    print(f"FBI command available: {fbi_available}")
    
    if fbi_available:
        try:
            result = subprocess.run(["fbi", "--help"], capture_output=True, timeout=5)
            print(f"FBI help command result: {result.returncode == 0}")
        except:
            print("FBI help command failed")
    
    # Check framebuffer availability
    fb_devices = [f"/dev/fb{i}" for i in range(4)]
    available_fb = [fb for fb in fb_devices if os.path.exists(fb)]
    print(f"Available framebuffer devices: {available_fb}")
    
    # Check Pygame availability
    try:
        import pygame
        pygame.init()
        pygame.display.init()
        print("Pygame available: True")
        
        # Get available display modes
        try:
            modes = pygame.display.list_modes()
            print(f"Available display modes: {modes[:5]}...")  # Show first 5
        except:
            print("Could not list display modes")
        
        pygame.quit()
    except ImportError:
        print("Pygame available: False")
    except Exception as e:
        print(f"Pygame test failed: {e}")
    
    # Check screen resolution detection methods
    print("\nTesting resolution detection methods:")
    
    # Test fbset
    try:
        result = subprocess.run(["fbset", "-s"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("fbset available and working")
            print(f"fbset output sample: {result.stdout[:100]}...")
        else:
            print("fbset available but failed")
    except:
        print("fbset not available")
    
    # Test xrandr
    try:
        result = subprocess.run(["xrandr", "--current"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("xrandr available and working")
            print(f"xrandr output sample: {result.stdout[:100]}...")
        else:
            print("xrandr available but failed")
    except:
        print("xrandr not available")


if __name__ == "__main__":
    print("DisplayController Example Script")
    print("================================")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check-methods":
        test_display_methods_availability()
    else:
        print("Running full DisplayController test...")
        print("Use --check-methods to only check available display methods")
        print()
        test_display_controller()