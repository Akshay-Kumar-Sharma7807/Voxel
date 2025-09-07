# Freepik AI Setup for Voxel Image Generation

This guide will help you set up Freepik AI for image generation, which offers high-quality AI-generated images with competitive pricing.

## Quick Start

If you already have a Freepik API key:

1. Add your API key to `.env` file:
   ```
   FREEPIK_API_KEY=your-freepik-api-key-here
   IMAGE_PROVIDER=freepik
   ```

2. Test the setup:
   ```bash
   python examples/test_image_generator.py
   ```

3. Run the application:
   ```bash
   python voxel.py
   ```

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
2. Apply for API access through their developer portal
3. You may need to:
   - Provide information about your use case
   - Wait for approval (usually 1-3 business days)
   - Verify your account and payment method
4. Once approved, you'll receive your API key in your developer dashboard

### 3. Set Environment Variables

**Option A: Using .env file (Recommended)**

Create or edit the `.env` file in your project root:

```bash
# Freepik Configuration
FREEPIK_API_KEY=your-freepik-api-key-here
IMAGE_PROVIDER=freepik
```

**Option B: System Environment Variables**

```bash
# Windows (Command Prompt)
set FREEPIK_API_KEY=your-freepik-api-key-here
set IMAGE_PROVIDER=freepik

# Windows (PowerShell)
$env:FREEPIK_API_KEY="your-freepik-api-key-here"
$env:IMAGE_PROVIDER="freepik"

# Linux/Mac
export FREEPIK_API_KEY=your-freepik-api-key-here
export IMAGE_PROVIDER=freepik
```

**Important Notes:**
- Replace `your-freepik-api-key-here` with your actual API key from Freepik
- Keep your API key secure and never commit it to version control
- The API key format is typically: `FPSXa880f10bb79585e8a4a082cb5ce5e8ac` (example)

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

### Common Setup Issues

#### 1. API Key Not Working
**Problem:** Getting authentication errors or "Invalid API key"

**Solutions:**
```bash
# Verify your API key format (should start with "FPSX")
echo $FREEPIK_API_KEY

# Test API key manually
curl -H "X-Freepik-API-Key: YOUR_API_KEY" https://api.freepik.com/v1/ai/text-to-image

# Check .env file format (no spaces around =)
cat .env | grep FREEPIK
```

#### 2. Environment Variables Not Loading
**Problem:** API key not being read from .env file

**Solutions:**
```bash
# Verify .env file exists in project root
ls -la .env

# Check file contents
cat .env

# Restart application after changing .env
python voxel.py
```

#### 3. Provider Not Set to Freepik
**Problem:** System still using OpenAI or other provider

**Solutions:**
```bash
# Verify IMAGE_PROVIDER is set correctly
grep IMAGE_PROVIDER .env

# Should show: IMAGE_PROVIDER=freepik
```

### API-Related Issues

#### Rate Limit Issues
- Check your plan's rate limits in Freepik dashboard
- Monitor usage to avoid hitting limits
- Consider upgrading your plan for higher limits
- The system includes automatic retry logic

#### Image Quality Issues
- Increase `num_inference_steps` (1-8) in config
- Adjust `guidance_scale` (1-20) for prompt adherence
- Try different models: flux, flux-realism, mystic
- Experiment with different styles and lighting options

#### Connection Issues
```bash
# Test internet connectivity to Freepik
ping api.freepik.com

# Check if firewall is blocking requests
curl -I https://api.freepik.com/v1/ai/text-to-image
```

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