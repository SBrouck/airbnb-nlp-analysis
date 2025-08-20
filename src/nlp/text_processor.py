"""
Text processing module for Airbnb reviews analysis.
Handles sentiment analysis, topic modeling, and key phrase extraction.
"""

import pandas as pd
import numpy as np
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from textblob import TextBlob
import spacy
from collections import Counter
from typing import List, Dict, Tuple, Optional
import logging

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AirbnbTextProcessor:
    """Class for processing Airbnb review text data."""
    
    def __init__(self, language_model: str = 'en_core_web_sm'):
        """
        Initialize the text processor.
        
        Args:
            language_model: spaCy language model to use
        """
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Add Airbnb-specific stop words
        self.stop_words.update([
            'airbnb', 'host', 'guest', 'stay', 'stayed', 'staying',
            'place', 'house', 'apartment', 'room', 'home', 'property',
            'booking', 'reservation', 'check', 'checkin', 'checkout'
        ])
        
        # Load spaCy model
        try:
            self.nlp = spacy.load(language_model)
        except OSError:
            logger.warning(f"spaCy model {language_model} not found. Installing...")
            import subprocess
            subprocess.run(['python', '-m', 'spacy', 'download', language_model])
            self.nlp = spacy.load(language_model)
    
    def clean_text(self, text: str) -> str:
        """
        Clean and preprocess text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if pd.isna(text) or text == '':
            return ''
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove special characters but keep apostrophes and hyphens
        text = re.sub(r'[^a-zA-Z0-9\s\'-]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize_and_lemmatize(self, text: str) -> List[str]:
        """
        Tokenize and lemmatize text.
        
        Args:
            text: Cleaned text
            
        Returns:
            List of lemmatized tokens
        """
        if not text:
            return []
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Lemmatize and filter
        lemmatized_tokens = []
        for token in tokens:
            if len(token) > 2 and token.lower() not in self.stop_words:
                lemmatized = self.lemmatizer.lemmatize(token.lower())
                lemmatized_tokens.append(lemmatized)
        
        return lemmatized_tokens
    
    def extract_sentiment(self, text: str) -> Dict[str, float]:
        """
        Extract sentiment scores from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with polarity and subjectivity scores
        """
        if not text:
            return {'polarity': 0.0, 'subjectivity': 0.0}
        
        blob = TextBlob(text)
        return {
            'polarity': blob.sentiment.polarity,
            'subjectivity': blob.sentiment.subjectivity
        }
    
    def extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[Tuple[str, float]]:
        """
        Extract key phrases from text using spaCy.
        
        Args:
            text: Text to analyze
            max_phrases: Maximum number of phrases to return
            
        Returns:
            List of (phrase, score) tuples
        """
        if not text:
            return []
        
        doc = self.nlp(text)
        
        # Extract noun phrases and named entities
        phrases = []
        
        # Noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= 2:  # At least 2 words
                phrases.append(chunk.text.lower())
        
        # Named entities
        for ent in doc.ents:
            if ent.label_ in ['LOC', 'ORG', 'PERSON', 'FAC']:
                phrases.append(ent.text.lower())
        
        # Count frequencies
        phrase_counts = Counter(phrases)
        
        # Return top phrases with scores
        return phrase_counts.most_common(max_phrases)
    
    def extract_amenities_mentioned(self, text: str) -> List[str]:
        """
        Extract amenities mentioned in the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of mentioned amenities
        """
        amenities_keywords = {
            'kitchen': ['kitchen', 'cooking', 'stove', 'oven', 'microwave', 'refrigerator'],
            'wifi': ['wifi', 'internet', 'wireless', 'connection'],
            'parking': ['parking', 'garage', 'car', 'vehicle'],
            'air_conditioning': ['ac', 'air conditioning', 'cooling', 'heating'],
            'laundry': ['laundry', 'washer', 'dryer', 'washing machine'],
            'pool': ['pool', 'swimming'],
            'gym': ['gym', 'fitness', 'exercise', 'workout'],
            'balcony': ['balcony', 'terrace', 'patio', 'deck'],
            'elevator': ['elevator', 'lift'],
            'breakfast': ['breakfast', 'coffee', 'tea'],
            'pets': ['pet', 'dog', 'cat', 'animal'],
            'smoking': ['smoking', 'smoke'],
            'accessibility': ['accessible', 'wheelchair', 'disability']
        }
        
        text_lower = text.lower()
        mentioned_amenities = []
        
        for amenity, keywords in amenities_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    mentioned_amenities.append(amenity)
                    break
        
        return mentioned_amenities
    
    def extract_location_features(self, text: str) -> List[str]:
        """
        Extract location-related features mentioned in the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of location features
        """
        location_keywords = {
            'downtown': ['downtown', 'city center', 'central'],
            'public_transport': ['train', 'bus', 'metro', 'subway', 'transit', 'transportation'],
            'walking_distance': ['walk', 'walking', 'close', 'near', 'nearby'],
            'restaurants': ['restaurant', 'food', 'dining', 'cafe', 'bar'],
            'shopping': ['shop', 'store', 'mall', 'market', 'grocery'],
            'attractions': ['attraction', 'museum', 'park', 'beach', 'tourist'],
            'university': ['university', 'college', 'campus', 'student'],
            'airport': ['airport', 'flight'],
            'highway': ['highway', 'freeway', 'road', 'street']
        }
        
        text_lower = text.lower()
        location_features = []
        
        for feature, keywords in location_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    location_features.append(feature)
                    break
        
        return location_features
    
    def extract_host_qualities(self, text: str) -> List[str]:
        """
        Extract host-related qualities mentioned in the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of host qualities
        """
        host_qualities = {
            'responsive': ['responsive', 'quick', 'fast', 'immediate', 'prompt'],
            'friendly': ['friendly', 'nice', 'kind', 'welcoming', 'warm'],
            'helpful': ['helpful', 'assist', 'support', 'guide', 'recommend'],
            'professional': ['professional', 'organized', 'efficient', 'thorough'],
            'communicative': ['communicate', 'clear', 'informative', 'detailed'],
            'flexible': ['flexible', 'accommodating', 'understanding'],
            'knowledgeable': ['knowledge', 'local', 'expert', 'insider'],
            'attentive': ['attentive', 'careful', 'thoughtful', 'considerate']
        }
        
        text_lower = text.lower()
        qualities = []
        
        for quality, keywords in host_qualities.items():
            for keyword in keywords:
                if keyword in text_lower:
                    qualities.append(quality)
                    break
        
        return qualities
    
    def extract_problem_areas(self, text: str) -> List[str]:
        """
        Extract problem areas mentioned in the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of problem areas
        """
        problem_keywords = {
            'noise': ['noise', 'loud', 'quiet', 'sound'],
            'cleanliness': ['clean', 'dirty', 'mess', 'tidy', 'hygiene'],
            'temperature': ['hot', 'cold', 'temperature', 'heating', 'cooling'],
            'smell': ['smell', 'odor', 'fragrance', 'scent'],
            'comfort': ['comfortable', 'uncomfortable', 'bed', 'sleep'],
            'safety': ['safe', 'security', 'lock', 'secure'],
            'maintenance': ['broken', 'repair', 'maintenance', 'issue', 'problem'],
            'communication': ['communication', 'response', 'contact', 'reach']
        }
        
        text_lower = text.lower()
        problems = []
        
        for problem, keywords in problem_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    problems.append(problem)
                    break
        
        return problems
    
    def process_reviews_batch(self, reviews_df: pd.DataFrame, 
                            text_column: str = 'comments_clean',
                            batch_size: int = 1000) -> pd.DataFrame:
        """
        Process a batch of reviews with all text analysis features.
        
        Args:
            reviews_df: DataFrame containing reviews
            text_column: Column name containing review text
            batch_size: Number of reviews to process at once
            
        Returns:
            DataFrame with added analysis columns
        """
        logger.info(f"Processing {len(reviews_df)} reviews...")
        
        processed_data = []
        
        for i in range(0, len(reviews_df), batch_size):
            batch = reviews_df.iloc[i:i+batch_size].copy()
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(reviews_df) + batch_size - 1)//batch_size}")
            
            # Clean text
            batch['text_clean'] = batch[text_column].apply(self.clean_text)
            
            # Extract sentiment
            sentiment_results = batch['text_clean'].apply(self.extract_sentiment)
            batch['sentiment_polarity'] = [r['polarity'] for r in sentiment_results]
            batch['sentiment_subjectivity'] = [r['subjectivity'] for r in sentiment_results]
            
            # Extract features
            batch['amenities_mentioned'] = batch['text_clean'].apply(self.extract_amenities_mentioned)
            batch['location_features'] = batch['text_clean'].apply(self.extract_location_features)
            batch['host_qualities'] = batch['text_clean'].apply(self.extract_host_qualities)
            batch['problem_areas'] = batch['text_clean'].apply(self.extract_problem_areas)
            
            # Tokenize for further analysis
            batch['tokens'] = batch['text_clean'].apply(self.tokenize_and_lemmatize)
            batch['token_count'] = batch['tokens'].apply(len)
            
            processed_data.append(batch)
        
        result_df = pd.concat(processed_data, ignore_index=True)
        logger.info("Text processing completed!")
        
        return result_df
    
    def generate_text_summary(self, processed_df: pd.DataFrame) -> Dict:
        """
        Generate a summary of text analysis results.
        
        Args:
            processed_df: Processed reviews DataFrame
            
        Returns:
            Dictionary with analysis summary
        """
        summary = {
            'total_reviews': len(processed_df),
            'avg_sentiment_polarity': processed_df['sentiment_polarity'].mean(),
            'avg_sentiment_subjectivity': processed_df['sentiment_subjectivity'].mean(),
            'avg_token_count': processed_df['token_count'].mean(),
            
            'most_common_amenities': self._get_most_common_features(processed_df, 'amenities_mentioned'),
            'most_common_location_features': self._get_most_common_features(processed_df, 'location_features'),
            'most_common_host_qualities': self._get_most_common_features(processed_df, 'host_qualities'),
            'most_common_problems': self._get_most_common_features(processed_df, 'problem_areas'),
            
            'sentiment_distribution': {
                'positive': len(processed_df[processed_df['sentiment_polarity'] > 0.1]),
                'neutral': len(processed_df[(processed_df['sentiment_polarity'] >= -0.1) & 
                                          (processed_df['sentiment_polarity'] <= 0.1)]),
                'negative': len(processed_df[processed_df['sentiment_polarity'] < -0.1])
            }
        }
        
        return summary
    
    def _get_most_common_features(self, df: pd.DataFrame, column: str, top_n: int = 10) -> List[Tuple[str, int]]:
        """Helper method to get most common features from a list column."""
        all_features = []
        for features in df[column]:
            all_features.extend(features)
        
        return Counter(all_features).most_common(top_n) 