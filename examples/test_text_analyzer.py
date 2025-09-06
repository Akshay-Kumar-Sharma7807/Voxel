"""
Example script demonstrating TextAnalyzer functionality.
"""

from datetime import datetime
from voxel.analysis import TextAnalyzer
from voxel.models import TranscriptionResult


def main():
    """Demonstrate text analysis with various examples."""
    analyzer = TextAnalyzer()
    
    # Example conversations to analyze
    examples = [
        {
            "text": "I'm so excited about our family vacation to the mountains! We're going hiking and camping under the stars.",
            "description": "Positive nature/family conversation"
        },
        {
            "text": "Working on this new AI project with machine learning algorithms. The code is complex but fascinating.",
            "description": "Technology-focused conversation"
        },
        {
            "text": "Feeling really stressed about the deadline. This project has been giving me so many problems.",
            "description": "Negative work-related conversation"
        },
        {
            "text": "The meeting is scheduled for tomorrow at 3 PM. Please review the quarterly reports beforehand.",
            "description": "Neutral business conversation"
        },
        {
            "text": "My heart is full of joy spending time with friends and family. Love brings such beautiful moments.",
            "description": "Emotional/relationship conversation"
        },
        {
            "text": "Playing basketball with the team, then going to watch a movie and grab dinner together.",
            "description": "Activities and social conversation"
        }
    ]
    
    print("=== TextAnalyzer Demonstration ===\n")
    
    for i, example in enumerate(examples, 1):
        print(f"Example {i}: {example['description']}")
        print(f"Text: \"{example['text']}\"")
        print("-" * 60)
        
        # Create transcription result
        transcription = TranscriptionResult(
            text=example['text'],
            confidence=0.85,
            timestamp=datetime.now(),
            is_valid=True
        )
        
        # Analyze the text
        result = analyzer.analyze_text(transcription)
        
        # Display results
        print(f"Keywords: {', '.join(result.keywords) if result.keywords else 'None'}")
        print(f"Sentiment: {result.sentiment}")
        print(f"Themes: {', '.join(result.themes) if result.themes else 'None'}")
        print(f"Confidence: {result.confidence:.2f}")
        print("\n" + "=" * 80 + "\n")
    
    # Demonstrate edge cases
    print("=== Edge Cases ===\n")
    
    edge_cases = [
        {
            "text": "",
            "description": "Empty text",
            "is_valid": True
        },
        {
            "text": "um uh yeah okay",
            "description": "Low-quality speech with filler words",
            "is_valid": True
        },
        {
            "text": "This is a test",
            "description": "Invalid transcription",
            "is_valid": False
        }
    ]
    
    for i, case in enumerate(edge_cases, 1):
        print(f"Edge Case {i}: {case['description']}")
        print(f"Text: \"{case['text']}\"")
        print("-" * 40)
        
        transcription = TranscriptionResult(
            text=case['text'],
            confidence=0.5,
            timestamp=datetime.now(),
            is_valid=case['is_valid']
        )
        
        result = analyzer.analyze_text(transcription)
        
        print(f"Keywords: {', '.join(result.keywords) if result.keywords else 'None'}")
        print(f"Sentiment: {result.sentiment}")
        print(f"Themes: {', '.join(result.themes) if result.themes else 'None'}")
        print(f"Confidence: {result.confidence:.2f}")
        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()