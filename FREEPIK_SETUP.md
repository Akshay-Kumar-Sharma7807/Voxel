# Freepik AI Setup for Voxel Image Generation

This guide will help you set up Freepik AI for image generation, which offers high-quality AI-generated images with competitive pricing.

## Prerequisites

1. **Freepik Account** (free or premium)
2. **Freepik API Access** (requires subscription)

## Step-by-Step Setup

### 1. Create Freepik Account

1. Visit [Freepik.com](https://www.freepik.com)
2. Sign up for an account or log in
3. Consider upgrading to Premium for better API access

### 2. Get API Access

1. Visit [Freepik API Documentation](https://freepik.com/api)
2. Apply for API access (may require approval)
3. Once approved, you'll receive your API key

### 3. Set Environment Variables

Create a `.env` file in your project root:

```bash
# Freepik Configuration
FREEPIK_API_KEY=your-freepik-api-key-here
IMAGE_PROVIDER=freepik
```

Or set them in your system:

```bash
# Windows
set FREEPIK_API_KEY=your-freepik-api-key-here
set IMAGE_PROVIDER=freepik

# Linux/Mac
export FREEPIK_API_KEY=your-freepik-api-key-here
export IMAGE_PROVIDER=freepik
```

### 4. Test the Setup

```bash
python examples/test_image_generator.py
```

## Freepik AI Features

### Available Models
- **flux**: General purpose, fast generation
- **flux-realism**: Photorealistic images
- **mystic**: Artistic and creative styles

### Response Format
Freepik API returns images as base64-encoded data:
```json
{
  "data": [
    {
      "base64": "iVBORw0KGgoAAAANSUhEUgAA...",
      "has_nsfw": false
    }
  ],
  "meta": {
    "image": {"size": "square_1_1", "width": 1024, "height": 1024},
    "seed": 42,
    "guidance_scale": 2,
    "prompt": "Your prompt here",
    "num_inference_steps": 8
  }
}
```

### Image Sizes
- `square_1_1`: 1024x1024 (recommended)
- `portrait_3_4`: 768x1024
- `portrait_9_16`: 576x1024
- `landscape_4_3`: 1024x768
- `landscape_16_9`: 1024x576

### Styles
- `photo`: Photographic style
- `digital-art`: Digital artwork
- `painting`: Traditional painting style
- `illustration`: Illustration style
- `anime`: Anime/manga style

### Effects Options
- **Color**: `vibrant`, `pastel`, `monochrome`
- **Lightning**: `warm`, `cold`, `studio`, `ambient`, `neon`
- **Framing**: `portrait`, `landscape`, `close-up`, `medium`, `full-body`

### Additional Features
- **Negative Prompts**: Specify what you don't want in the image
- **Guidance Scale**: Control adherence to prompt (1-20)
- **Seed**: For reproducible results
- **NSFW Filter**: Automatic content filtering

## Configuration Options

You can customize Freepik settings in `voxel/config.py`:

```python
# Freepik AI configuration
FREEPIK_IMAGE_SIZE = "square_1_1"  # See sizes above
FREEPIK_STYLE = "photo"  # See styles above
FREEPIK_LIGHTING = "warm"  # See effects options above
FREEPIK_FRAMING = "portrait"  # See effects options above
FREEPIK_GUIDANCE_SCALE = 2.0  # 1-20, higher = more prompt adherence
FREEPIK_COLOR_EFFECT = "vibrant"  # vibrant, pastel, monochrome
```

## Pricing

Freepik AI pricing (as of 2024):
- **Free Plan**: Limited API calls
- **Premium Plan**: ~$10-15/month with API access
- **Enterprise**: Custom pricing for high volume

Check current pricing: [Freepik Pricing](https://www.freepik.com/pricing)

## API Limits

- **Rate Limits**: Varies by plan (typically 100-1000 requests/hour)
- **Monthly Limits**: Based on subscription tier
- **Image Resolution**: Up to 1024x1024 on premium plans

## Advantages of Freepik AI

### Pros
- **High Quality**: Excellent image quality with multiple models
- **Affordable**: Competitive pricing compared to other providers
- **Variety**: Multiple styles, lighting, and framing options
- **Fast**: Quick generation times
- **Reliable**: Stable API with good uptime

### Best For
- **Creative Projects**: Great for artistic and creative content
- **Marketing Materials**: Professional-quality images for marketing
- **Ambient Art**: Perfect for mood-based ambient art generation
- **Prototyping**: Quick visual prototypes and concepts

## Troubleshooting

### Authentication Issues
```bash
# Verify your API key is correct
curl -H "X-Freepik-API-Key: YOUR_API_KEY" https://api.freepik.com/v1/ai/text-to-image
```

### Rate Limit Issues
- Check your plan's rate limits
- Implement proper retry logic (already included)
- Consider upgrading your plan for higher limits

### Image Quality Issues
- Increase `num_inference_steps` (1-8)
- Adjust `guidance_scale` (1-20)
- Try different models (flux, flux-realism, mystic)
- Experiment with different styles and lighting

## Example Usage

```python
from voxel.generation.generator import ImageGenerator
from voxel.models import ImagePrompt, AnalysisResult
from datetime import datetime

# Create generator with Freepik
generator = ImageGenerator(provider="freepik")

# Create prompt
analysis = AnalysisResult(
    keywords=["sunset", "peaceful", "nature"],
    sentiment="positive",
    themes=["nature"],
    confidence=0.9
)

prompt = ImagePrompt(
    prompt_text="A peaceful sunset over calm waters with warm colors",
    style_modifiers=["peaceful", "warm"],
    source_analysis=analysis,
    timestamp=datetime.now()
)

# Generate image
result = generator.generate_image(prompt)
print(f"Image saved to: {result.local_path}")
```

## Security Best Practices

1. **Keep API Key Secret**: Never commit API keys to version control
2. **Use Environment Variables**: Store keys in environment variables
3. **Monitor Usage**: Track API usage to avoid unexpected charges
4. **Rotate Keys**: Regularly rotate API keys for security

## Support

- **Freepik API Docs**: [https://freepik.com/api](https://freepik.com/api)
- **Support**: Contact Freepik support for API issues
- **Community**: Freepik developer community and forums