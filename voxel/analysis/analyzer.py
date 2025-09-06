"""
Text analysis module for extracting keywords, sentiment, and themes from transcribed speech.
"""

import re
from collections import Counter
from typing import List, Dict, Set
from datetime import datetime

from ..models import AnalysisResult, TranscriptionResult


class TextAnalyzer:
    """
    Analyzes transcribed text to extract keywords, sentiment, and themes.
    """
    
    def __init__(self):
        """Initialize the text analyzer with word lists and patterns."""
        self._positive_words = {
            'happy', 'joy', 'love', 'great', 'amazing', 'wonderful', 'fantastic', 
            'excellent', 'good', 'beautiful', 'awesome', 'perfect', 'brilliant',
            'excited', 'thrilled', 'delighted', 'pleased', 'satisfied', 'grateful',
            'optimistic', 'cheerful', 'positive', 'success', 'win', 'victory',
            'celebrate', 'laugh', 'smile', 'fun', 'enjoy', 'like', 'appreciate'
        }
        
        self._negative_words = {
            'sad', 'angry', 'hate', 'terrible', 'awful', 'horrible', 'bad',
            'worst', 'disgusting', 'annoying', 'frustrated', 'disappointed',
            'upset', 'worried', 'anxious', 'stressed', 'depressed', 'angry',
            'furious', 'irritated', 'bothered', 'concerned', 'trouble', 'problem',
            'issue', 'fail', 'failure', 'lose', 'loss', 'wrong', 'mistake',
            'error', 'difficult', 'hard', 'struggle', 'pain', 'hurt'
        }
        
        # Common stop words to filter out
        self._stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
            'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'your', 'his', 'her', 'its', 'our', 'their', 'what', 'when',
            'where', 'why', 'how', 'who', 'which', 'there', 'here', 'now', 'then',
            'just', 'only', 'also', 'very', 'so', 'too', 'much', 'many', 'more',
            'most', 'some', 'any', 'all', 'no', 'not', 'yes', 'well', 'like',
            'get', 'got', 'go', 'going', 'come', 'came', 'see', 'saw', 'know',
            'knew', 'think', 'thought', 'say', 'said', 'tell', 'told', 'ask',
            'asked', 'give', 'gave', 'take', 'took', 'make', 'made', 'want',
            'wanted', 'need', 'needed', 'try', 'tried', 'use', 'used', 'work',
            'worked', 'look', 'looked', 'feel', 'felt', 'seem', 'seemed'
        }
        
        # Theme categories with associated keywords
        self._theme_keywords = {
            'nature': {
                'tree', 'trees', 'forest', 'mountain', 'mountains', 'river', 'ocean',
                'sea', 'beach', 'sky', 'cloud', 'clouds', 'sun', 'moon', 'star',
                'stars', 'flower', 'flowers', 'garden', 'park', 'animal', 'animals',
                'bird', 'birds', 'fish', 'water', 'rain', 'snow', 'wind', 'weather',
                'outdoor', 'outside', 'hiking', 'camping', 'nature', 'natural',
                'green', 'blue', 'peaceful', 'calm', 'serene'
            },
            'emotions': {
                'feel', 'feeling', 'feelings', 'emotion', 'emotions', 'mood',
                'happy', 'sad', 'angry', 'excited', 'nervous', 'calm', 'peaceful',
                'love', 'hate', 'like', 'dislike', 'joy', 'sorrow', 'fear',
                'hope', 'dream', 'dreams', 'wish', 'wishes', 'heart', 'soul',
                'mind', 'think', 'thinking', 'thoughts', 'remember', 'memory',
                'memories', 'forget', 'forgive', 'trust', 'believe', 'faith'
            },
            'activities': {
                'work', 'working', 'job', 'career', 'business', 'meeting', 'project',
                'task', 'play', 'playing', 'game', 'games', 'sport', 'sports',
                'exercise', 'run', 'running', 'walk', 'walking', 'drive', 'driving',
                'travel', 'traveling', 'trip', 'vacation', 'holiday', 'party',
                'celebration', 'dance', 'dancing', 'music', 'sing', 'singing',
                'read', 'reading', 'book', 'books', 'movie', 'movies', 'watch',
                'watching', 'cook', 'cooking', 'eat', 'eating', 'drink', 'drinking',
                'shop', 'shopping', 'buy', 'buying', 'sell', 'selling'
            },
            'relationships': {
                'family', 'friend', 'friends', 'relationship', 'relationships',
                'partner', 'husband', 'wife', 'boyfriend', 'girlfriend', 'mother',
                'father', 'mom', 'dad', 'parent', 'parents', 'child', 'children',
                'son', 'daughter', 'brother', 'sister', 'grandmother', 'grandfather',
                'grandma', 'grandpa', 'uncle', 'aunt', 'cousin', 'neighbor',
                'colleague', 'coworker', 'boss', 'team', 'group', 'community',
                'together', 'alone', 'social', 'talk', 'talking', 'conversation',
                'discuss', 'discussion', 'share', 'sharing', 'help', 'helping',
                'support', 'care', 'caring', 'kind', 'kindness'
            },
            'technology': {
                'computer', 'phone', 'mobile', 'internet', 'online', 'website',
                'app', 'application', 'software', 'program', 'code', 'coding',
                'digital', 'electronic', 'device', 'gadget', 'tech', 'technology',
                'ai', 'artificial', 'intelligence', 'robot', 'automation',
                'data', 'information', 'network', 'connection', 'wifi', 'bluetooth',
                'screen', 'display', 'keyboard', 'mouse', 'camera', 'video',
                'audio', 'sound', 'music', 'streaming', 'download', 'upload',
                'social', 'media', 'facebook', 'twitter', 'instagram', 'youtube'
            },
            'abstract': {
                'time', 'space', 'energy', 'power', 'force', 'light', 'dark',
                'darkness', 'bright', 'brightness', 'color', 'colors', 'shape',
                'shapes', 'pattern', 'patterns', 'texture', 'movement', 'motion',
                'speed', 'slow', 'fast', 'big', 'small', 'large', 'tiny', 'huge',
                'infinite', 'eternal', 'forever', 'never', 'always', 'sometimes',
                'maybe', 'perhaps', 'possible', 'impossible', 'real', 'reality',
                'dream', 'imagination', 'creative', 'creativity', 'art', 'artistic',
                'beauty', 'beautiful', 'ugly', 'strange', 'weird', 'normal',
                'different', 'same', 'similar', 'unique', 'special', 'ordinary'
            }
        }
    
    def analyze_text(self, transcription: TranscriptionResult) -> AnalysisResult:
        """
        Analyze transcribed text to extract keywords, sentiment, and themes.
        
        Args:
            transcription: The transcription result to analyze
            
        Returns:
            AnalysisResult containing keywords, sentiment, themes, and confidence
        """
        if not transcription.is_valid or not transcription.text.strip():
            return AnalysisResult(
                keywords=[],
                sentiment='neutral',
                themes=[],
                confidence=0.0
            )
        
        text = transcription.text.lower().strip()
        
        # Extract keywords
        keywords = self.extract_keywords(text)
        
        # Analyze sentiment
        sentiment = self.analyze_sentiment(text)
        
        # Generate themes
        themes = self.generate_themes(text, keywords)
        
        # Calculate overall confidence based on transcription confidence and content quality
        confidence = self._calculate_confidence(transcription.confidence, keywords, text)
        
        return AnalysisResult(
            keywords=keywords,
            sentiment=sentiment,
            themes=themes,
            confidence=confidence
        )
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract significant keywords from text using frequency analysis.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of extracted keywords, ordered by significance
        """
        # Clean and tokenize text
        words = self._tokenize_text(text)
        
        # Filter out stop words and short words
        filtered_words = [
            word for word in words 
            if word not in self._stop_words and len(word) > 2
        ]
        
        if not filtered_words:
            return []
        
        # Count word frequencies
        word_counts = Counter(filtered_words)
        
        # Get top keywords (up to 10, minimum frequency of 1)
        top_keywords = [
            word for word, count in word_counts.most_common(10)
            if count >= 1
        ]
        
        return top_keywords
    
    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of text using word lists and scoring.
        
        Args:
            text: The text to analyze
            
        Returns:
            Sentiment classification: 'positive', 'negative', or 'neutral'
        """
        words = self._tokenize_text(text)
        
        positive_score = sum(1 for word in words if word in self._positive_words)
        negative_score = sum(1 for word in words if word in self._negative_words)
        
        # Calculate sentiment based on score difference
        if positive_score > negative_score:
            return 'positive'
        elif negative_score > positive_score:
            return 'negative'
        else:
            return 'neutral'
    
    def generate_themes(self, text: str, keywords: List[str]) -> List[str]:
        """
        Generate thematic categories based on text content and keywords.
        
        Args:
            text: The original text
            keywords: Extracted keywords
            
        Returns:
            List of identified themes
        """
        words = self._tokenize_text(text)
        all_words = set(words + keywords)
        
        themes = []
        theme_scores = {}
        
        # Score each theme based on keyword matches
        for theme, theme_words in self._theme_keywords.items():
            matches = len(all_words.intersection(theme_words))
            if matches > 0:
                theme_scores[theme] = matches
        
        # Return themes sorted by relevance (highest matches first)
        if theme_scores:
            sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
            themes = [theme for theme, score in sorted_themes if score >= 1]
        
        return themes[:3]  # Return top 3 themes maximum
    
    def _tokenize_text(self, text: str) -> List[str]:
        """
        Tokenize text into individual words.
        
        Args:
            text: The text to tokenize
            
        Returns:
            List of lowercase words
        """
        # Remove punctuation and split into words
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return words
    
    def _calculate_confidence(self, transcription_confidence: float, keywords: List[str], text: str) -> float:
        """
        Calculate overall analysis confidence based on multiple factors.
        
        Args:
            transcription_confidence: Confidence from speech recognition
            keywords: Extracted keywords
            text: Original text
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Start with transcription confidence
        confidence = transcription_confidence
        
        # Adjust based on content quality
        word_count = len(self._tokenize_text(text))
        keyword_count = len(keywords)
        
        # Boost confidence if we have good content
        if word_count >= 5 and keyword_count >= 2:
            confidence = min(1.0, confidence + 0.1)
        elif word_count >= 3 and keyword_count >= 1:
            confidence = min(1.0, confidence + 0.05)
        
        # Reduce confidence for very short content
        if word_count < 3:
            confidence *= 0.7
        
        return max(0.0, min(1.0, confidence))