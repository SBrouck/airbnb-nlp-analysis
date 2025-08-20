#!/usr/bin/env python3
"""
Lightweight Airbnb Reviews Analysis for Business Insights
Optimized for processing large datasets efficiently without heavy NLP.
"""

import pandas as pd
import numpy as np
import re
from collections import Counter
import logging
from datetime import datetime
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LightweightAirbnbAnalyzer:
    """Lightweight analyzer for Airbnb reviews business insights."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the lightweight analyzer.
        
        Args:
            df: DataFrame containing reviews data
        """
        self.df = df.copy()
        self.insights = {}
        
        # Simple keyword patterns for analysis
        self.keywords = {
            'amenities': {
                'wifi': ['wifi', 'internet', 'wireless'],
                'kitchen': ['kitchen', 'cooking', 'stove', 'microwave'],
                'parking': ['parking', 'garage', 'car'],
                'ac': ['ac', 'air conditioning', 'cooling', 'heating'],
                'laundry': ['laundry', 'washer', 'dryer'],
                'pool': ['pool', 'swimming'],
                'gym': ['gym', 'fitness', 'exercise']
            },
            'host_qualities': {
                'responsive': ['responsive', 'quick', 'fast', 'prompt'],
                'friendly': ['friendly', 'nice', 'kind', 'welcoming'],
                'helpful': ['helpful', 'assist', 'support', 'guide'],
                'professional': ['professional', 'organized', 'efficient'],
                'communicative': ['communicate', 'clear', 'informative']
            },
            'problems': {
                'noise': ['noise', 'loud', 'quiet'],
                'cleanliness': ['clean', 'dirty', 'mess', 'tidy'],
                'temperature': ['hot', 'cold', 'temperature'],
                'smell': ['smell', 'odor'],
                'comfort': ['comfortable', 'uncomfortable', 'bed'],
                'safety': ['safe', 'security', 'lock']
            },
            'location': {
                'downtown': ['downtown', 'city center', 'central'],
                'transport': ['train', 'bus', 'metro', 'transit'],
                'walking': ['walk', 'walking', 'close', 'near'],
                'restaurants': ['restaurant', 'food', 'dining', 'cafe'],
                'shopping': ['shop', 'store', 'mall', 'market']
            }
        }
    
    def simple_sentiment_analysis(self, text: str) -> float:
        """
        Simple sentiment analysis using keyword counting.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment score (-1 to 1)
        """
        if pd.isna(text) or text == '':
            return 0.0
        
        text_lower = text.lower()
        
        # Positive keywords
        positive_words = [
            'great', 'excellent', 'amazing', 'wonderful', 'perfect', 'fantastic',
            'love', 'enjoy', 'beautiful', 'clean', 'comfortable', 'convenient',
            'friendly', 'helpful', 'responsive', 'recommend', 'stay again'
        ]
        
        # Negative keywords
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'dirty', 'noisy',
            'uncomfortable', 'disappointing', 'problem', 'issue', 'broken',
            'rude', 'unresponsive', 'never', 'avoid', 'complaint'
        ]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        # Normalize by text length
        sentiment = (positive_count - negative_count) / max(total_words, 10)
        return np.clip(sentiment, -1, 1)
    
    def extract_features(self, text: str, feature_type: str) -> list:
        """
        Extract features using simple keyword matching.
        
        Args:
            text: Text to analyze
            feature_type: Type of features to extract
            
        Returns:
            List of found features
        """
        if pd.isna(text) or text == '':
            return []
        
        text_lower = text.lower()
        found_features = []
        
        if feature_type in self.keywords:
            for feature, keywords in self.keywords[feature_type].items():
                if any(keyword in text_lower for keyword in keywords):
                    found_features.append(feature)
        
        return found_features
    
    def analyze_reviews(self, sample_size: int = None) -> dict:
        """
        Analyze reviews efficiently.
        
        Args:
            sample_size: Number of reviews to sample (for faster processing)
            
        Returns:
            Dictionary with analysis results
        """
        logger.info("Starting lightweight analysis...")
        
        # Sample data if specified
        if sample_size and sample_size < len(self.df):
            logger.info(f"Sampling {sample_size:,} reviews for analysis")
            df_sample = self.df.sample(n=sample_size, random_state=42).reset_index(drop=True)
        else:
            df_sample = self.df
        
        logger.info(f"Analyzing {len(df_sample):,} reviews...")
        
        # Simple sentiment analysis
        logger.info("Performing sentiment analysis...")
        df_sample['sentiment_score'] = df_sample['comments_clean'].apply(self.simple_sentiment_analysis)
        
        # Extract features
        logger.info("Extracting features...")
        for feature_type in ['amenities', 'host_qualities', 'problems', 'location']:
            df_sample[f'{feature_type}_mentioned'] = df_sample['comments_clean'].apply(
                lambda x: self.extract_features(x, feature_type)
            )
        
        # Calculate review length
        df_sample['comment_length'] = df_sample['comments_clean'].str.len()
        
        # Analyze sentiment distribution
        positive_reviews = df_sample[df_sample['sentiment_score'] > 0.05]
        negative_reviews = df_sample[df_sample['sentiment_score'] < -0.05]
        neutral_reviews = df_sample[(df_sample['sentiment_score'] >= -0.05) & 
                                  (df_sample['sentiment_score'] <= 0.05)]
        
        # Compile insights
        insights = {
            'overview': {
                'total_reviews': len(df_sample),
                'positive_reviews': len(positive_reviews),
                'negative_reviews': len(negative_reviews),
                'neutral_reviews': len(neutral_reviews),
                'positive_rate': len(positive_reviews) / len(df_sample) * 100,
                'avg_sentiment': df_sample['sentiment_score'].mean(),
                'avg_comment_length': df_sample['comment_length'].mean()
            },
            'amenities_analysis': self._analyze_amenities(df_sample),
            'host_qualities_analysis': self._analyze_host_qualities(df_sample),
            'problems_analysis': self._analyze_problems(df_sample),
            'location_analysis': self._analyze_location(df_sample),
            'seasonal_analysis': self._analyze_seasonal_patterns(df_sample)
        }
        
        self.insights = insights
        return insights
    
    def _analyze_amenities(self, df: pd.DataFrame) -> dict:
        """Analyze amenity mentions and their impact on sentiment."""
        amenity_impact = {}
        
        for amenity in self.keywords['amenities'].keys():
            amenity_reviews = df[df['amenities_mentioned'].apply(lambda x: amenity in x)]
            non_amenity_reviews = df[df['amenities_mentioned'].apply(lambda x: amenity not in x)]
            
            if len(amenity_reviews) > 0 and len(non_amenity_reviews) > 0:
                avg_with_amenity = amenity_reviews['sentiment_score'].mean()
                avg_without_amenity = non_amenity_reviews['sentiment_score'].mean()
                impact_score = avg_with_amenity - avg_without_amenity
                
                amenity_impact[amenity] = {
                    'impact_score': impact_score,
                    'avg_sentiment_with': avg_with_amenity,
                    'avg_sentiment_without': avg_without_amenity,
                    'mention_count': len(amenity_reviews),
                    'mention_percentage': len(amenity_reviews) / len(df) * 100
                }
        
        return {
            'amenity_impact': amenity_impact,
            'top_amenities': sorted(amenity_impact.items(), 
                                  key=lambda x: x[1]['impact_score'], reverse=True)
        }
    
    def _analyze_host_qualities(self, df: pd.DataFrame) -> dict:
        """Analyze host qualities mentioned in reviews."""
        quality_counts = Counter()
        
        for qualities in df['host_qualities_mentioned']:
            quality_counts.update(qualities)
        
        # Analyze by sentiment
        positive_qualities = Counter()
        negative_qualities = Counter()
        
        for idx, qualities in enumerate(df['host_qualities_mentioned']):
            if df.iloc[idx]['sentiment_score'] > 0.05:
                positive_qualities.update(qualities)
            elif df.iloc[idx]['sentiment_score'] < -0.05:
                negative_qualities.update(qualities)
        
        return {
            'all_qualities': quality_counts.most_common(10),
            'positive_qualities': positive_qualities.most_common(10),
            'negative_qualities': negative_qualities.most_common(10)
        }
    
    def _analyze_problems(self, df: pd.DataFrame) -> dict:
        """Analyze problems mentioned in reviews."""
        problem_counts = Counter()
        
        for problems in df['problems_mentioned']:
            problem_counts.update(problems)
        
        # Focus on negative reviews for problem analysis
        negative_reviews = df[df['sentiment_score'] < -0.05]
        negative_problems = Counter()
        
        for problems in negative_reviews['problems_mentioned']:
            negative_problems.update(problems)
        
        return {
            'all_problems': problem_counts.most_common(10),
            'negative_review_problems': negative_problems.most_common(10),
            'problem_frequency': {k: v/len(df)*100 for k, v in problem_counts.most_common(10)}
        }
    
    def _analyze_location(self, df: pd.DataFrame) -> dict:
        """Analyze location features mentioned in reviews."""
        location_impact = {}
        
        for location_feature in self.keywords['location'].keys():
            feature_reviews = df[df['location_mentioned'].apply(lambda x: location_feature in x)]
            non_feature_reviews = df[df['location_mentioned'].apply(lambda x: location_feature not in x)]
            
            if len(feature_reviews) > 0 and len(non_feature_reviews) > 0:
                avg_with_feature = feature_reviews['sentiment_score'].mean()
                avg_without_feature = non_feature_reviews['sentiment_score'].mean()
                impact_score = avg_with_feature - avg_without_feature
                
                location_impact[location_feature] = {
                    'impact_score': impact_score,
                    'avg_sentiment_with': avg_with_feature,
                    'avg_sentiment_without': avg_without_feature,
                    'mention_count': len(feature_reviews),
                    'mention_percentage': len(feature_reviews) / len(df) * 100
                }
        
        return {
            'location_impact': location_impact,
            'top_location_features': sorted(location_impact.items(), 
                                          key=lambda x: x[1]['impact_score'], reverse=True)
        }
    
    def _analyze_seasonal_patterns(self, df: pd.DataFrame) -> dict:
        """Analyze seasonal patterns in reviews."""
        if 'review_month' not in df.columns:
            return {'error': 'Review month data not available'}
        
        # Monthly sentiment analysis
        monthly_stats = df.groupby('review_month').agg({
            'sentiment_score': ['mean', 'count'],
            'comment_length': 'mean'
        }).round(3)
        
        # Flatten column names
        monthly_stats.columns = ['avg_sentiment', 'review_count', 'avg_length']
        
        # Find peak and low months
        peak_months = monthly_stats.sort_values('review_count', ascending=False).head(3).index.tolist()
        low_months = monthly_stats.sort_values('review_count').head(3).index.tolist()
        
        return {
            'monthly_stats': monthly_stats.to_dict(),
            'peak_months': peak_months,
            'low_months': low_months,
            'seasonal_sentiment': monthly_stats['avg_sentiment'].to_dict()
        }
    
    def generate_report(self, output_file: str = None) -> str:
        """
        Generate a comprehensive business insights report.
        
        Args:
            output_file: Optional file path to save the report
            
        Returns:
            String containing the report
        """
        if not self.insights:
            raise ValueError("No insights available. Run analyze_reviews() first.")
        
        report = []
        report.append("=" * 80)
        report.append("AIRBNB BUSINESS INSIGHTS REPORT (Lightweight Analysis)")
        report.append("=" * 80)
        report.append("")
        
        # Overview
        overview = self.insights['overview']
        report.append("1. OVERVIEW")
        report.append("-" * 20)
        report.append(f"Total Reviews Analyzed: {overview['total_reviews']:,}")
        report.append(f"Positive Reviews: {overview['positive_reviews']:,} ({overview['positive_rate']:.1f}%)")
        report.append(f"Negative Reviews: {overview['negative_reviews']:,}")
        report.append(f"Average Sentiment Score: {overview['avg_sentiment']:.3f}")
        report.append(f"Average Comment Length: {overview['avg_comment_length']:.0f} characters")
        report.append("")
        
        # Amenities Analysis
        report.append("2. AMENITIES ANALYSIS")
        report.append("-" * 25)
        report.append("Most Valued Amenities (by sentiment impact):")
        for amenity, data in self.insights['amenities_analysis']['top_amenities'][:5]:
            report.append(f"  • {amenity}: {data['impact_score']:.3f} impact score ({data['mention_percentage']:.1f}% mentions)")
        report.append("")
        
        # Host Qualities
        report.append("3. HOST QUALITIES")
        report.append("-" * 20)
        report.append("Top Host Qualities (Positive Reviews):")
        for quality, count in self.insights['host_qualities_analysis']['positive_qualities'][:5]:
            report.append(f"  • {quality}: {count} mentions")
        report.append("")
        
        # Problems
        report.append("4. COMMON PROBLEMS")
        report.append("-" * 20)
        report.append("Most Common Issues (Negative Reviews):")
        for problem, count in self.insights['problems_analysis']['negative_review_problems'][:5]:
            report.append(f"  • {problem}: {count} mentions")
        report.append("")
        
        # Location
        report.append("5. LOCATION FEATURES")
        report.append("-" * 25)
        report.append("Most Valued Location Features:")
        for feature, data in self.insights['location_analysis']['top_location_features'][:5]:
            report.append(f"  • {feature}: {data['impact_score']:.3f} impact score ({data['mention_percentage']:.1f}% mentions)")
        report.append("")
        
        # Seasonal Patterns
        if 'seasonal_analysis' in self.insights and 'peak_months' in self.insights['seasonal_analysis']:
            report.append("6. SEASONAL PATTERNS")
            report.append("-" * 25)
            report.append(f"Peak Months: {self.insights['seasonal_analysis']['peak_months']}")
            report.append(f"Low Season Months: {self.insights['seasonal_analysis']['low_months']}")
            report.append("")
        
        # Business Recommendations
        report.append("7. BUSINESS RECOMMENDATIONS")
        report.append("-" * 30)
        report.append("• Focus on responsive and friendly communication")
        report.append("• Prioritize basic amenities: WiFi, kitchen, parking")
        report.append("• Emphasize location benefits and accessibility")
        report.append("• Address cleanliness and noise issues proactively")
        report.append("• Consider seasonal pricing strategies")
        report.append("• Maintain professional and organized operations")
        
        report_text = "\n".join(report)
        
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(report_text)
        
        return report_text


def main():
    """Main function to run the lightweight analysis."""
    print("=" * 80)
    print("AIRBNB REVIEWS LIGHTWEIGHT ANALYSIS")
    print("=" * 80)
    print()
    
    # Check if data file exists
    data_path = "data/raw/cleaned_reviews.csv"
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        print("Please ensure the cleaned_reviews.csv file is in the data/raw/ directory.")
        return
    
    try:
        # Load data
        print("Loading data...")
        df = pd.read_csv(data_path)
        print(f"Loaded {len(df):,} reviews")
        
        # Ask user for sample size
        print("\nChoose analysis scope:")
        print("1. Quick sample (10,000 reviews) - ~30 seconds")
        print("2. Medium sample (50,000 reviews) - ~2 minutes")
        print("3. Large sample (200,000 reviews) - ~8 minutes")
        print("4. Full dataset (all reviews) - ~30 minutes")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        sample_sizes = {
            '1': 10000,
            '2': 50000,
            '3': 200000,
            '4': None
        }
        
        sample_size = sample_sizes.get(choice, 10000)
        
        if sample_size:
            print(f"\nRunning analysis on {sample_size:,} reviews...")
        else:
            print(f"\nRunning analysis on all {len(df):,} reviews...")
        
        # Initialize analyzer
        analyzer = LightweightAirbnbAnalyzer(df)
        
        # Run analysis
        insights = analyzer.analyze_reviews(sample_size=sample_size)
        
        # Generate report
        report_path = "reports/lightweight_business_insights.txt"
        report = analyzer.generate_report(report_path)
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print()
        print("Key Results:")
        print(f"• Positive Review Rate: {insights['overview']['positive_rate']:.1f}%")
        print(f"• Average Sentiment: {insights['overview']['avg_sentiment']:.3f}")
        print(f"• Total Reviews Analyzed: {insights['overview']['total_reviews']:,}")
        print()
        print("Generated files:")
        print(f"• {report_path} - Detailed business insights report")
        print()
        print("Top insights:")
        if insights['amenities_analysis']['top_amenities']:
            top_amenity = insights['amenities_analysis']['top_amenities'][0]
            print(f"• Most valued amenity: {top_amenity[0]} (impact: {top_amenity[1]['impact_score']:.3f})")
        
        if insights['host_qualities_analysis']['positive_qualities']:
            top_quality = insights['host_qualities_analysis']['positive_qualities'][0]
            print(f"• Top host quality: {top_quality[0]} ({top_quality[1]} mentions)")
        
        print("\nCheck the reports directory for the complete analysis!")
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Please check the logs for more details.")


if __name__ == "__main__":
    main() 