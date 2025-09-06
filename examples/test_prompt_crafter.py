"""
Example script demonstrating the PromptCrafter functionality.
"""

from datetime import datetime
from voxel.generation.crafter import PromptCrafter
from voxel.models import AnalysisResult


def main():
    """Demonstrate PromptCrafter with various analysis scenarios."""
    
    print("=== Voxel PromptCrafter Demo ===\n")
    
    # Initialize the prompt crafter
    crafter = PromptCrafter()
    
    # Test scenarios with different analysis results
    test_scenarios = [
        {
            'name': 'Nature Conversation (Positive)',
            'analysis': AnalysisResult(
                keywords=['trees', 'forest', 'peaceful', 'walking', 'birds'],
                sentiment='positive',
                themes=['nature', 'activities'],
                confidence=0.85
            )
        },
        {
            'name': 'Work Discussion (Negative)',
            'analysis': AnalysisResult(
                keywords=['work', 'stress', 'deadline', 'difficult', 'tired'],
                sentiment='negative',
                themes=['activities', 'emotions'],
                confidence=0.75
            )
        },
        {
            'name': 'Technology Talk (Neutral)',
            'analysis': AnalysisResult(
                keywords=['computer', 'internet', 'digital', 'software', 'data'],
                sentiment='neutral',
                themes=['technology'],
                confidence=0.70
            )
        },
        {
            'name': 'Family Time (Positive)',
            'analysis': AnalysisResult(
                keywords=['family', 'home', 'children', 'love', 'together'],
                sentiment='positive',
                themes=['relationships', 'emotions'],
                confidence=0.80
            )
        },
        {
            'name': 'Abstract Discussion (Neutral)',
            'analysis': AnalysisResult(
                keywords=['time', 'space', 'thinking', 'ideas', 'future'],
                sentiment='neutral',
                themes=['abstract'],
                confidence=0.65
            )
        },
        {
            'name': 'Low Quality Input',
            'analysis': AnalysisResult(
                keywords=[],
                sentiment='neutral',
                themes=[],
                confidence=0.20
            )
        }
    ]
    
    # Process each scenario
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"{i}. {scenario['name']}")
        print("-" * 50)
        
        analysis = scenario['analysis']
        
        # Display analysis input
        print(f"Input Analysis:")
        print(f"  Keywords: {analysis.keywords}")
        print(f"  Sentiment: {analysis.sentiment}")
        print(f"  Themes: {analysis.themes}")
        print(f"  Confidence: {analysis.confidence:.2f}")
        print()
        
        # Generate prompt
        prompt = crafter.craft_prompt(analysis)
        
        # Display generated prompt
        print(f"Generated Prompt:")
        print(f"  Text: {prompt.prompt_text}")
        print(f"  Style Modifiers: {prompt.style_modifiers}")
        print()
        
        # Validate prompt
        is_valid = crafter.validate_prompt_format(prompt)
        print(f"Prompt Validation: {'✓ VALID' if is_valid else '✗ INVALID'}")
        
        # Get style suggestions
        suggestions = crafter.get_style_suggestions(analysis.themes, analysis.sentiment)
        print(f"Style Suggestions: {suggestions[:3]}")  # Show first 3
        
        print("\n" + "="*70 + "\n")
    
    # Demonstrate prompt enhancement
    print("=== Prompt Enhancement Demo ===\n")
    
    # Test with problematic content
    test_analysis = AnalysisResult(
        keywords=['person', 'face', 'people'],
        sentiment='neutral',
        themes=['relationships'],
        confidence=0.6
    )
    
    prompt = crafter.craft_prompt(test_analysis)
    print(f"Original prompt with potentially problematic keywords:")
    print(f"Keywords: {test_analysis.keywords}")
    print(f"Generated: {prompt.prompt_text}")
    print()
    
    # Test sanitization directly
    problematic_text = "A painting of a person with a face and other people"
    sanitized = crafter._sanitize_prompt(problematic_text)
    print(f"Direct sanitization test:")
    print(f"Original: {problematic_text}")
    print(f"Sanitized: {sanitized}")
    print()
    
    # Test enhancement
    short_prompt = "Art"
    enhanced_short = crafter._enhance_prompt_quality(short_prompt)
    print(f"Short prompt enhancement:")
    print(f"Original: {short_prompt}")
    print(f"Enhanced: {enhanced_short}")
    print()
    
    long_prompt = "A beautiful painting " * 50  # Very long
    enhanced_long = crafter._enhance_prompt_quality(long_prompt)
    print(f"Long prompt enhancement:")
    print(f"Original length: {len(long_prompt)} characters")
    print(f"Enhanced length: {len(enhanced_long)} characters")
    print(f"Enhanced: {enhanced_long[:100]}...")
    print()
    
    print("=== Demo Complete ===")


if __name__ == '__main__':
    main()