"""
Unit tests for the TextAnalyzer class.
"""

import unittest
from datetime import datetime

from voxel.analysis import TextAnalyzer
from voxel.models import TranscriptionResult, AnalysisResult


class TestTextAnalyzer(unittest.TestCase):
    """Test cases for TextAnalyzer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = TextAnalyzer()
        self.timestamp = datetime.now()
    
    def _create_transcription(self, text: str, confidence: float = 0.8, is_valid: bool = True) -> TranscriptionResult:
        """Helper method to create TranscriptionResult objects."""
        return TranscriptionResult(
            text=text,
            confidence=confidence,
            timestamp=self.timestamp,
            is_valid=is_valid
        )
    
    def test_analyze_empty_text(self):
        """Test analysis of empty or invalid text."""
        # Test empty text
        transcription = self._create_transcription("", 0.8, True)
        result = self.analyzer.analyze_text(transcription)
        
        self.assertEqual(result.keywords, [])
        self.assertEqual(result.sentiment, 'neutral')
        self.assertEqual(result.themes, [])
        self.assertEqual(result.confidence, 0.0)
        
        # Test invalid transcription
        transcription = self._create_transcription("some text", 0.8, False)
        result = self.analyzer.analyze_text(transcription)
        
        self.assertEqual(result.keywords, [])
        self.assertEqual(result.sentiment, 'neutral')
        self.assertEqual(result.themes, [])
        self.assertEqual(result.confidence, 0.0)
    
    def test_keyword_extraction_basic(self):
        """Test basic keyword extraction functionality."""
        text = "I love programming computers and building software applications"
        transcription = self._create_transcription(text)
        result = self.analyzer.analyze_text(transcription)
        
        # Should extract meaningful keywords, filtering out stop words
        self.assertIn('programming', result.keywords)
        self.assertIn('computers', result.keywords)
        self.assertIn('building', result.keywords)
        self.assertIn('software', result.keywords)
        self.assertIn('applications', result.keywords)
        
        # Should not include stop words
        self.assertNotIn('i', result.keywords)
        self.assertNotIn('and', result.keywords)
    
    def test_keyword_extraction_frequency(self):
        """Test keyword extraction with word frequency."""
        text = "The cat sat on the mat. The cat was happy. The cat played with the ball."
        transcription = self._create_transcription(text)
        result = self.analyzer.analyze_text(transcription)
        
        # 'cat' appears 3 times, should be top keyword
        self.assertIn('cat', result.keywords)
        # Should be first due to frequency
        self.assertEqual(result.keywords[0], 'cat')
    
    def test_keyword_extraction_short_words_filtered(self):
        """Test that short words (<=2 characters) are filtered out."""
        text = "I go to my car and we do it"
        transcription = self._create_transcription(text)
        result = self.analyzer.analyze_text(transcription)
        
        # Should not include short words like 'go', 'to', 'my', 'we', 'do', 'it'
        short_words = ['go', 'to', 'my', 'we', 'do', 'it']
        for word in short_words:
            self.assertNotIn(word, result.keywords)
        
        # Should include longer words
        self.assertIn('car', result.keywords)
    
    def test_sentiment_analysis_positive(self):
        """Test positive sentiment detection."""
        positive_texts = [
            "I am so happy and excited about this wonderful day",
            "This is amazing and fantastic, I love it",
            "Great job everyone, this is excellent work",
            "Beautiful weather today, feeling grateful and optimistic"
        ]
        
        for text in positive_texts:
            transcription = self._create_transcription(text)
            result = self.analyzer.analyze_text(transcription)
            self.assertEqual(result.sentiment, 'positive', f"Failed for text: {text}")
    
    def test_sentiment_analysis_negative(self):
        """Test negative sentiment detection."""
        negative_texts = [
            "I am so sad and angry about this terrible situation",
            "This is awful and horrible, I hate it",
            "Bad news everyone, this is the worst",
            "Frustrated and disappointed with these problems"
        ]
        
        for text in negative_texts:
            transcription = self._create_transcription(text)
            result = self.analyzer.analyze_text(transcription)
            self.assertEqual(result.sentiment, 'negative', f"Failed for text: {text}")
    
    def test_sentiment_analysis_neutral(self):
        """Test neutral sentiment detection."""
        neutral_texts = [
            "The meeting is scheduled for tomorrow at three",
            "Please review the document and send feedback",
            "The weather forecast shows rain this weekend",
            "We need to discuss the project timeline"
        ]
        
        for text in neutral_texts:
            transcription = self._create_transcription(text)
            result = self.analyzer.analyze_text(transcription)
            self.assertEqual(result.sentiment, 'neutral', f"Failed for text: {text}")
    
    def test_sentiment_analysis_mixed(self):
        """Test sentiment analysis with mixed positive and negative words."""
        # Equal positive and negative words should result in neutral
        text = "I love this project but I hate the deadline pressure"
        transcription = self._create_transcription(text)
        result = self.analyzer.analyze_text(transcription)
        self.assertEqual(result.sentiment, 'neutral')
        
        # More positive than negative
        text = "I love this amazing project even though there are some problems"
        transcription = self._create_transcription(text)
        result = self.analyzer.analyze_text(transcription)
        self.assertEqual(result.sentiment, 'positive')
    
    def test_theme_generation_nature(self):
        """Test nature theme detection."""
        text = "Walking through the forest, I saw beautiful trees and heard birds singing near the river"
        transcription = self._create_transcription(text)
        result = self.analyzer.analyze_text(transcription)
        
        self.assertIn('nature', result.themes)
    
    def test_theme_generation_technology(self):
        """Test technology theme detection."""
        text = "Working on my computer, coding a new mobile app with artificial intelligence features"
        transcription = self._create_transcription(text)
        result = self.analyzer.analyze_text(transcription)
        
        self.assertIn('technology', result.themes)
    
    def test_theme_generation_emotions(self):
        """Test emotions theme detection."""
        text = "Feeling happy and excited, my heart is full of joy and love for my family"
        transcription = self._create_transcription(text)
        result = self.analyzer.analyze_text(transcription)
        
        self.assertIn('emotions', result.themes)
    
    def test_theme_generation_activities(self):
        """Test activities theme detection."""
        text = "Going to work today, then playing sports and watching a movie tonight"
        transcription = self._create_transcription(text)
        result = self.analyzer.analyze_text(transcription)
        
        self.assertIn('activities', result.themes)
    
    def test_theme_generation_relationships(self):
        """Test relationships theme detection."""
        text = "Talking with my family and friends, helping my colleagues at work"
        transcription = self._create_transcription(text)
        result = self.analyzer.analyze_text(transcription)
        
        self.assertIn('relationships', result.themes)
    
    def test_theme_generation_multiple_themes(self):
        """Test detection of multiple themes in one text."""
        text = "Working on my computer with friends, feeling excited about our nature photography project"
        transcription = self._create_transcription(text)
        result = self.analyzer.analyze_text(transcription)
        
        # Should detect multiple themes
        self.assertTrue(len(result.themes) > 1)
        # Should limit to maximum 3 themes
        self.assertTrue(len(result.themes) <= 3)
    
    def test_theme_generation_no_themes(self):
        """Test text with no clear themes."""
        text = "The quick brown fox jumps over the lazy dog"
        transcription = self._create_transcription(text)
        result = self.analyzer.analyze_text(transcription)
        
        # Should return empty themes list for generic text
        self.assertEqual(result.themes, [])
    
    def test_confidence_calculation_high_quality(self):
        """Test confidence calculation for high-quality content."""
        text = "I am working on an exciting programming project with artificial intelligence and machine learning"
        transcription = self._create_transcription(text, confidence=0.9)
        result = self.analyzer.analyze_text(transcription)
        
        # Should have high confidence due to good transcription and rich content
        self.assertGreater(result.confidence, 0.8)
    
    def test_confidence_calculation_low_quality(self):
        """Test confidence calculation for low-quality content."""
        # Short text with low transcription confidence
        text = "um yeah"
        transcription = self._create_transcription(text, confidence=0.3)
        result = self.analyzer.analyze_text(transcription)
        
        # Should have reduced confidence
        self.assertLess(result.confidence, 0.5)
    
    def test_confidence_calculation_medium_quality(self):
        """Test confidence calculation for medium-quality content."""
        text = "Going to the store today"
        transcription = self._create_transcription(text, confidence=0.7)
        result = self.analyzer.analyze_text(transcription)
        
        # Should have moderate confidence
        self.assertGreater(result.confidence, 0.5)
        self.assertLess(result.confidence, 0.9)
    
    def test_tokenization(self):
        """Test text tokenization functionality."""
        text = "Hello, world! How are you today? I'm fine, thanks."
        words = self.analyzer._tokenize_text(text)
        
        expected_words = ['hello', 'world', 'how', 'are', 'you', 'today', 'i', 'm', 'fine', 'thanks']
        self.assertEqual(words, expected_words)
    
    def test_tokenization_special_characters(self):
        """Test tokenization with special characters and numbers."""
        text = "Email me at user@example.com or call 555-1234!"
        words = self.analyzer._tokenize_text(text)
        
        # Should only include alphabetic words
        for word in words:
            self.assertTrue(word.isalpha(), f"Non-alphabetic word found: {word}")
    
    def test_comprehensive_analysis(self):
        """Test comprehensive analysis with realistic conversation text."""
        text = """
        Hey everyone, I'm so excited to share that we're planning a camping trip 
        to the mountains next weekend. The weather looks beautiful and we'll be 
        hiking through the forest and taking photos of wildlife. My family and 
        friends are all coming together for this amazing adventure. I love spending 
        time in nature, it makes me feel peaceful and happy.
        """
        
        transcription = self._create_transcription(text, confidence=0.85)
        result = self.analyzer.analyze_text(transcription)
        
        # Should extract some relevant keywords (not necessarily all due to frequency-based selection)
        expected_keywords = ['camping', 'mountains', 'hiking', 'forest', 'wildlife', 'family', 'friends', 'nature']
        found_keywords = set(result.keywords)
        expected_keywords_set = set(expected_keywords)
        
        # Should find at least 2 of the expected keywords (realistic for frequency-based extraction)
        intersection = found_keywords.intersection(expected_keywords_set)
        self.assertGreaterEqual(len(intersection), 2, 
                               f"Expected at least 2 keywords from {expected_keywords}, but only found {list(intersection)} in {result.keywords}")
        
        # Should have extracted a reasonable number of keywords
        self.assertGreater(len(result.keywords), 5)
        
        # Should detect positive sentiment
        self.assertEqual(result.sentiment, 'positive')
        
        # Should identify relevant themes
        expected_themes = ['nature', 'activities', 'relationships', 'emotions']
        found_themes = set(result.themes)
        expected_themes_set = set(expected_themes)
        
        # Should find at least some of the expected themes
        self.assertTrue(len(found_themes.intersection(expected_themes_set)) >= 2,
                       f"Expected to find at least 2 themes from {expected_themes}, but got {result.themes}")
        
        # Should have good confidence
        self.assertGreater(result.confidence, 0.7)


if __name__ == '__main__':
    unittest.main()