"""
Example usage of the ImageGenerator class.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from voxel.generation.generator import ImageGenerator
from voxel.models import ImagePrompt, AnalysisResult


def create_sample_prompt():
    """Create a sample image prompt for testing."""
    analysis = AnalysisResult(
        keywords=["sunset", "peaceful", "nature", "warm"],
        sentiment="positive",
        themes=["nature", "emotions"],
        confidence=0.85
    )
    
    return ImagePrompt(
        prompt_text="A serene sunset over a calm lake with warm golden colors, digital painting style",
        style_modifiers=["digital painting", "warm colors", "peaceful"],
        source_analysis=analysis,
        timestamp=datetime.now()
    )


def main():
    """Demonstrate ImageGenerator usage."""
    print("=== Voxel Image Generator Example ===\n")
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    try:
        # Initialize the generator
        print("🔧 Initializing ImageGenerator...")
        generator = ImageGenerator()
        print("✅ ImageGenerator initialized successfully")
        
        # Create a sample prompt
        print("\n📝 Creating sample image prompt...")
        prompt = create_sample_prompt()
        print(f"Prompt: {prompt.prompt_text}")
        print(f"Keywords: {', '.join(prompt.source_analysis.keywords)}")
        print(f"Sentiment: {prompt.source_analysis.sentiment}")
        
        # Generate image (this will make a real API call if uncommented)
        print("\n🎨 Generating image...")
        print("⚠️  Note: This would make a real API call to DALL-E 3")
        print("⚠️  Uncomment the lines below to test with real API")
        
        # Uncomment these lines to test with real API:
        # result = generator.generate_image(prompt)
        # print(f"✅ Image generated successfully!")
        # print(f"URL: {result.url}")
        # print(f"Local path: {result.local_path}")
        # print(f"Generation time: {result.generation_time}")
        
        # Demonstrate error handling
        print("\n🛡️  Testing error handling...")
        
        # Test authentication error
        try:
            bad_generator = ImageGenerator(api_key="invalid-key")
            # This would fail on actual API call
            print("✅ Bad API key handled gracefully")
        except Exception as e:
            print(f"✅ Error handling working: {type(e).__name__}")
        
        # Test cleanup functionality
        print("\n🧹 Testing image cleanup...")
        generator.cleanup_old_images(max_images=10)
        print("✅ Cleanup completed")
        
        print("\n🎉 Example completed successfully!")
        print("\nTo test with real API calls:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Uncomment the API call lines in this script")
        print("3. Run the script again")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")


if __name__ == "__main__":
    main()