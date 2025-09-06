"""
Artistic prompt generation module for creating DALL-E 3 compatible image prompts.
"""

import random
from typing import List, Dict, Set
from datetime import datetime

from ..models import AnalysisResult, ImagePrompt


class PromptCrafter:
    """
    Transforms conversation analysis into artistic image generation prompts.
    """
    
    def __init__(self):
        """Initialize the prompt crafter with artistic templates and modifiers."""
        
        # Base artistic styles
        self._artistic_styles = [
            "digital painting",
            "watercolor painting",
            "oil painting",
            "Studio Ghibli style",
            "impressionist painting",
            "abstract art",
            "minimalist art",
            "surreal art",
            "ambient art",
            "atmospheric painting",
            "dreamy illustration",
            "ethereal artwork"
        ]
        
        # Mood-based color palettes
        self._color_palettes = {
            'positive': [
                "warm golden tones",
                "bright vibrant colors",
                "soft pastel hues",
                "sunny yellow and orange palette",
                "cheerful rainbow colors",
                "warm sunset colors",
                "gentle spring colors",
                "uplifting bright palette"
            ],
            'negative': [
                "cool blue and gray tones",
                "muted dark colors",
                "stormy gray palette",
                "deep purple and black tones",
                "somber earth tones",
                "melancholic blue hues",
                "shadowy dark palette",
                "moody atmospheric colors"
            ],
            'neutral': [
                "balanced natural colors",
                "soft earth tones",
                "gentle neutral palette",
                "calm beige and brown hues",
                "peaceful natural colors",
                "subtle color harmony",
                "serene balanced tones",
                "quiet contemplative colors"
            ]
        }
        
        # Theme-based scene elements
        self._theme_elements = {
            'nature': [
                "flowing rivers and mountains",
                "ancient forests with dappled light",
                "peaceful meadows with wildflowers",
                "misty mountain landscapes",
                "serene lake reflections",
                "gentle ocean waves",
                "rustling leaves in wind",
                "starlit night sky"
            ],
            'emotions': [
                "swirling emotional energy",
                "abstract forms expressing feelings",
                "flowing shapes representing mood",
                "ethereal light patterns",
                "dancing particles of emotion",
                "waves of consciousness",
                "floating dream-like elements",
                "gentle emotional currents"
            ],
            'activities': [
                "dynamic movement and energy",
                "rhythmic patterns of activity",
                "flowing lines of motion",
                "energetic swirls and shapes",
                "bustling life patterns",
                "active geometric forms",
                "vibrant activity streams",
                "lively compositional elements"
            ],
            'relationships': [
                "interconnected flowing forms",
                "harmonious interweaving patterns",
                "gentle connecting elements",
                "warm embracing shapes",
                "unified compositional harmony",
                "bonding light connections",
                "caring protective forms",
                "loving energy flows"
            ],
            'technology': [
                "sleek digital patterns",
                "glowing circuit-like designs",
                "futuristic geometric forms",
                "flowing data streams",
                "luminous technological elements",
                "modern abstract networks",
                "digital light patterns",
                "cyber-organic hybrid forms"
            ],
            'abstract': [
                "flowing abstract forms",
                "mysterious ethereal shapes",
                "infinite space patterns",
                "timeless flowing energy",
                "cosmic swirling elements",
                "dreamlike abstract composition",
                "surreal floating forms",
                "transcendent light patterns"
            ]
        }
        
        # Composition and atmosphere modifiers
        self._composition_modifiers = [
            "soft ambient lighting",
            "gentle atmospheric perspective",
            "dreamy bokeh effects",
            "flowing organic composition",
            "harmonious balance",
            "peaceful symmetry",
            "dynamic asymmetrical flow",
            "serene minimalist space",
            "rich textural depth",
            "luminous transparency effects"
        ]
        
        # Quality enhancement keywords for DALL-E 3
        self._quality_modifiers = [
            "high quality",
            "detailed",
            "artistic",
            "beautiful",
            "atmospheric",
            "professional",
            "masterpiece",
            "stunning"
        ]
        
        # Prompt templates
        self._prompt_templates = [
            "A {style} depicting {scene_elements} with {color_palette}, featuring {composition}, {quality}",
            "{quality} {style} of {scene_elements} in {color_palette} with {composition}",
            "An {quality} {style} showing {scene_elements}, rendered in {color_palette} with {composition}",
            "{style} artwork featuring {scene_elements} and {color_palette}, {composition}, {quality}",
            "A {quality} {style} composition of {scene_elements} using {color_palette} and {composition}"
        ]
    
    def craft_prompt(self, analysis: AnalysisResult) -> ImagePrompt:
        """
        Generate an artistic image prompt from conversation analysis.
        
        Args:
            analysis: The analysis result containing keywords, sentiment, and themes
            
        Returns:
            ImagePrompt ready for DALL-E 3 generation
        """
        if analysis.confidence < 0.3 or not analysis.keywords:
            # Generate a default ambient prompt for low-quality input
            return self._create_default_prompt(analysis)
        
        # Select artistic elements based on analysis
        style = self._select_artistic_style()
        color_palette = self._select_color_palette(analysis.sentiment)
        scene_elements = self._generate_scene_elements(analysis.themes, analysis.keywords)
        composition = self._select_composition_modifier()
        quality = self._select_quality_modifier()
        
        # Build the prompt using a template
        template = random.choice(self._prompt_templates)
        prompt_text = template.format(
            style=style,
            scene_elements=scene_elements,
            color_palette=color_palette,
            composition=composition,
            quality=quality
        )
        
        # Apply style modifiers
        style_modifiers = [style, color_palette, composition, quality]
        
        # Enhance and validate the prompt
        enhanced_prompt = self._enhance_prompt_quality(prompt_text)
        
        return ImagePrompt(
            prompt_text=enhanced_prompt,
            style_modifiers=style_modifiers,
            source_analysis=analysis,
            timestamp=datetime.now()
        )
    
    def _select_artistic_style(self) -> str:
        """Select an artistic style randomly."""
        return random.choice(self._artistic_styles)
    
    def _select_color_palette(self, sentiment: str) -> str:
        """
        Select a color palette based on sentiment.
        
        Args:
            sentiment: The sentiment classification ('positive', 'negative', 'neutral')
            
        Returns:
            Color palette description
        """
        palettes = self._color_palettes.get(sentiment, self._color_palettes['neutral'])
        return random.choice(palettes)
    
    def _generate_scene_elements(self, themes: List[str], keywords: List[str]) -> str:
        """
        Generate scene elements based on themes and keywords.
        
        Args:
            themes: List of identified themes
            keywords: List of extracted keywords
            
        Returns:
            Scene elements description
        """
        scene_parts = []
        
        # Add theme-based elements
        for theme in themes[:2]:  # Use top 2 themes
            if theme in self._theme_elements:
                element = random.choice(self._theme_elements[theme])
                scene_parts.append(element)
        
        # If no themes or need more elements, use keywords creatively
        if len(scene_parts) < 2 and keywords:
            # Transform keywords into artistic elements
            keyword_elements = self._transform_keywords_to_elements(keywords[:3])
            scene_parts.extend(keyword_elements)
        
        # Fallback to abstract elements if still empty
        if not scene_parts:
            scene_parts = [random.choice(self._theme_elements['abstract'])]
        
        # Combine elements naturally
        if len(scene_parts) == 1:
            return scene_parts[0]
        elif len(scene_parts) == 2:
            return f"{scene_parts[0]} and {scene_parts[1]}"
        else:
            return f"{', '.join(scene_parts[:-1])}, and {scene_parts[-1]}"
    
    def _transform_keywords_to_elements(self, keywords: List[str]) -> List[str]:
        """
        Transform conversation keywords into artistic scene elements.
        
        Args:
            keywords: List of keywords to transform
            
        Returns:
            List of artistic elements
        """
        elements = []
        
        for keyword in keywords:
            # Create artistic interpretations of keywords
            if keyword in ['work', 'job', 'business']:
                elements.append("flowing patterns of productivity")
            elif keyword in ['home', 'house', 'family']:
                elements.append("warm embracing forms")
            elif keyword in ['music', 'song', 'sound']:
                elements.append("rhythmic visual harmonies")
            elif keyword in ['food', 'eat', 'cooking']:
                elements.append("nourishing organic shapes")
            elif keyword in ['travel', 'trip', 'journey']:
                elements.append("wandering pathways of discovery")
            elif keyword in ['friend', 'friends', 'people']:
                elements.append("interconnected flowing energies")
            elif keyword in ['time', 'day', 'night']:
                elements.append("temporal light transitions")
            elif keyword in ['weather', 'rain', 'sun']:
                elements.append("atmospheric elemental forces")
            else:
                # Generic transformation for other keywords
                elements.append(f"abstract representations of {keyword}")
        
        return elements[:2]  # Limit to 2 elements to avoid overcrowding
    
    def _select_composition_modifier(self) -> str:
        """Select a composition modifier randomly."""
        return random.choice(self._composition_modifiers)
    
    def _select_quality_modifier(self) -> str:
        """Select a quality modifier randomly."""
        return random.choice(self._quality_modifiers)
    
    def _enhance_prompt_quality(self, prompt: str) -> str:
        """
        Enhance and validate prompt quality for DALL-E 3 compatibility.
        
        Args:
            prompt: The initial prompt text
            
        Returns:
            Enhanced prompt text
        """
        # Ensure prompt is not too long (DALL-E 3 has limits)
        if len(prompt) > 1000:
            # Truncate while preserving meaning
            words = prompt.split()
            while len(' '.join(words)) > 1000 and len(words) > 10:
                words.pop()
            prompt = ' '.join(words)
        
        # Ensure prompt is not too short
        if len(prompt) < 50:
            prompt += ", beautiful artistic composition, high quality"
        
        # Remove any potentially problematic content
        prompt = self._sanitize_prompt(prompt)
        
        return prompt
    
    def _sanitize_prompt(self, prompt: str) -> str:
        """
        Remove potentially problematic content from prompts.
        
        Args:
            prompt: The prompt to sanitize
            
        Returns:
            Sanitized prompt
        """
        # Remove any explicit references to people, brands, or copyrighted content
        # This is a basic implementation - could be expanded
        
        # Replace potentially problematic words with artistic alternatives
        replacements = {
            'person': 'figure',
            'people': 'figures',
            'man': 'figure',
            'woman': 'figure',
            'child': 'small figure',
            'face': 'abstract form',
            'faces': 'abstract forms'
        }
        
        words = prompt.split()
        for i, word in enumerate(words):
            clean_word = word.lower().strip('.,!?;:')
            if clean_word in replacements:
                # Preserve original capitalization and punctuation
                replacement = replacements[clean_word]
                if word[0].isupper():
                    replacement = replacement.capitalize()
                # Add back punctuation
                for punct in '.,!?;:':
                    if word.endswith(punct):
                        replacement += punct
                        break
                words[i] = replacement
        
        return ' '.join(words)
    
    def _create_default_prompt(self, analysis: AnalysisResult) -> ImagePrompt:
        """
        Create a default ambient prompt for low-quality or empty analysis.
        
        Args:
            analysis: The analysis result (may be low quality)
            
        Returns:
            Default ImagePrompt
        """
        default_prompts = [
            "A peaceful abstract composition with flowing organic forms in soft natural colors, gentle atmospheric lighting, high quality digital art",
            "Serene ambient artwork featuring ethereal light patterns and calm flowing shapes in harmonious earth tones, beautiful atmospheric painting",
            "Tranquil abstract landscape with gentle color gradients and soft organic forms, dreamy impressionist style, high quality",
            "Peaceful flowing composition with subtle color transitions and organic abstract elements, serene atmospheric art",
            "Calm ambient artwork with soft flowing forms and gentle natural colors, ethereal digital painting, beautiful and serene"
        ]
        
        prompt_text = random.choice(default_prompts)
        
        return ImagePrompt(
            prompt_text=prompt_text,
            style_modifiers=["ambient art", "peaceful", "abstract", "high quality"],
            source_analysis=analysis,
            timestamp=datetime.now()
        )
    
    def validate_prompt_format(self, prompt: ImagePrompt) -> bool:
        """
        Validate that the prompt is compatible with DALL-E 3 requirements.
        
        Args:
            prompt: The ImagePrompt to validate
            
        Returns:
            True if prompt is valid, False otherwise
        """
        text = prompt.prompt_text
        
        # Check length constraints
        if len(text) < 10 or len(text) > 1000:
            return False
        
        # Check for required elements
        if not text.strip():
            return False
        
        # Check for potentially problematic content
        problematic_terms = [
            'nude', 'naked', 'explicit', 'violence', 'weapon', 'gun', 'blood',
            'political', 'celebrity', 'brand name', 'logo', 'trademark'
        ]
        
        text_lower = text.lower()
        for term in problematic_terms:
            if term in text_lower:
                return False
        
        return True
    
    def get_style_suggestions(self, themes: List[str], sentiment: str) -> List[str]:
        """
        Get style suggestions based on themes and sentiment.
        
        Args:
            themes: List of identified themes
            sentiment: Sentiment classification
            
        Returns:
            List of suggested artistic styles
        """
        suggestions = []
        
        # Add sentiment-appropriate styles
        if sentiment == 'positive':
            suggestions.extend([
                "bright impressionist painting",
                "cheerful Studio Ghibli style",
                "vibrant digital art"
            ])
        elif sentiment == 'negative':
            suggestions.extend([
                "moody atmospheric painting",
                "melancholic abstract art",
                "somber watercolor"
            ])
        else:
            suggestions.extend([
                "peaceful ambient art",
                "serene minimalist composition",
                "calm ethereal artwork"
            ])
        
        # Add theme-appropriate styles
        for theme in themes:
            if theme == 'nature':
                suggestions.append("organic landscape painting")
            elif theme == 'technology':
                suggestions.append("futuristic digital art")
            elif theme == 'emotions':
                suggestions.append("expressive abstract composition")
        
        return list(set(suggestions))  # Remove duplicates