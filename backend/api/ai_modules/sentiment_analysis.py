"""
Sentiment Analysis Module
Uses HuggingFace BERT model (nlptown/bert-base-multilingual-uncased-sentiment)
for multilingual sentiment analysis with ratings 1-5 converted to -1, 0, +1 scores.
Falls back to TextBlob if BERT model fails to load.
"""

from textblob import TextBlob
import re

# Try to load HuggingFace transformers
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    BERT_AVAILABLE = True
except ImportError:
    BERT_AVAILABLE = False
    print("Warning: transformers/torch not available, using TextBlob fallback")


class BERTSentimentAnalyzer:
    """
    Sentiment analyzer using nlptown/bert-base-multilingual-uncased-sentiment
    Returns ratings 1-5 and converts to sentiment scores: -1, 0, +1
    """
    
    def __init__(self):
        self.model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
        self.model_version = "bert_multilingual_v1.0"
        self.tokenizer = None
        self.model = None
        self._loaded = False
        
    def load_model(self):
        """Load the BERT tokenizer and model"""
        if self._loaded:
            return True
        
        if not BERT_AVAILABLE:
            print("BERT dependencies not available")
            return False
            
        try:
            print(f"Loading BERT sentiment model: {self.model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.eval()  # Set to evaluation mode
            self._loaded = True
            print("BERT sentiment model loaded successfully!")
            return True
        except Exception as e:
            print(f"Failed to load BERT model: {e}")
            return False
    
    def clean_text(self, text):
        """Clean text for analysis"""
        if not text:
            return ""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Truncate to model max length (512 tokens roughly)
        if len(text) > 500:
            text = text[:500]
        return text
    
    def predict_rating(self, text):
        """
        Predict sentiment rating from 1 to 5
        
        Args:
            text: Input text (news title, content, or comment)
            
        Returns:
            int: Rating from 1 (most negative) to 5 (most positive)
        """
        if not self._loaded:
            if not self.load_model():
                return 3  # Neutral fallback
        
        cleaned_text = self.clean_text(text)
        if not cleaned_text:
            return 3  # Neutral for empty text
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                cleaned_text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            # Get model prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                
            # Get the predicted class (0-4) and convert to rating (1-5)
            predicted_class = torch.argmax(predictions, dim=-1).item()
            rating = predicted_class + 1  # Convert 0-4 to 1-5
            
            return rating
            
        except Exception as e:
            print(f"BERT prediction error: {e}")
            return 3  # Neutral fallback
    
    def rating_to_sentiment_score(self, rating):
        """
        Convert rating (1-5) to sentiment score (-1, 0, +1)
        
        Args:
            rating: int from 1 to 5
            
        Returns:
            int: -1 (negative), 0 (neutral), or +1 (positive)
        """
        if rating <= 2:
            return -1  # Negative (ratings 1-2)
        elif rating >= 4:
            return 1   # Positive (ratings 4-5)
        else:
            return 0   # Neutral (rating 3)
    
    def analyze(self, text):
        """
        Analyze sentiment of text using BERT model
        
        Args:
            text: Input text (news title, content, or comment)
            
        Returns:
            dict: Contains rating (1-5), sentiment_score (-1, 0, +1), and label
        """
        rating = self.predict_rating(text)
        sentiment_score = self.rating_to_sentiment_score(rating)
        
        # Determine label
        if sentiment_score == 1:
            label = 'positive'
        elif sentiment_score == -1:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'rating': rating,
            'sentiment_score': sentiment_score,
            'label': label
        }
    
    def get_sentiment_score(self, text):
        """
        Get just the sentiment score for backward compatibility
        
        Args:
            text: Input text
            
        Returns:
            float: Normalized score between -1 and 1
        """
        rating = self.predict_rating(text)
        # Convert 1-5 rating to -1 to 1 scale
        return (rating - 3) / 2.0
    
    def analyze_batch(self, texts):
        """Analyze sentiment for multiple texts"""
        return [self.analyze(text) for text in texts]


class SentimentAnalyzer:
    """Legacy analyzer using TextBlob (fallback)"""
    
    def __init__(self):
        self.model_version = "textblob_v1.0"
    
    def clean_text(self, text):
        """Clean text for analysis"""
        if not text:
            return ""
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = ' '.join(text.split())
        return text
    
    def analyze(self, text):
        """
        Analyze sentiment of text
        Returns: float between -1 and 1
        """
        if not text:
            return 0.0
        
        cleaned_text = self.clean_text(text)
        
        try:
            blob = TextBlob(cleaned_text)
            sentiment_score = blob.sentiment.polarity
            return round(sentiment_score, 3)
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return 0.0
    
    def analyze_batch(self, texts):
        """Analyze sentiment for multiple texts"""
        return [self.analyze(text) for text in texts]
    
    def categorize_sentiment(self, score):
        """Categorize sentiment score into positive, neutral, negative"""
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'


# Global instances
bert_analyzer = BERTSentimentAnalyzer()
sentiment_analyzer = SentimentAnalyzer()  # Fallback


def analyze_sentiment_bert(text):
    """
    Analyze sentiment using BERT model (nlptown/bert-base-multilingual-uncased-sentiment)
    
    Args:
        text: Input text (news title, content, or comment)
        
    Returns:
        dict: Contains rating (1-5), sentiment_score (-1, 0, +1), and label
    """
    return bert_analyzer.analyze(text)


def analyze_sentiment(text):
    """
    Convenience function for quick sentiment analysis
    Uses TextBlob (lightweight, avoids loading the heavy BERT model
    which exceeds free-tier memory limits)

    Returns: float between -1 and 1
    """
    return sentiment_analyzer.analyze(text)


def analyze_article_sentiment(article_data):
    """Analyze sentiment of a news article"""
    title = article_data.get('title') or ''
    description = article_data.get('description') or article_data.get('summary') or ''
    content = article_data.get('content') or ''
    text = f"{title} {description} {content}"
    return analyze_sentiment(text)


# ============================================================
# EXAMPLE USAGE
# ============================================================
if __name__ == "__main__":
    # Example showing how to use the BERT sentiment analyzer
    
    print("=" * 60)
    print("BERT Sentiment Analysis Example")
    print("Model: nlptown/bert-base-multilingual-uncased-sentiment")
    print("=" * 60)
    
    # Sample texts to analyze
    sample_texts = [
        "This is absolutely amazing news! I'm so happy about this breakthrough.",
        "The market crashed today, causing widespread panic and losses.",
        "The weather forecast predicts cloudy skies tomorrow.",
        "Terrible service, worst experience ever. Never coming back!",
        "Great product, highly recommended! Five stars!",
    ]
    
    # Initialize and load the BERT analyzer
    analyzer = BERTSentimentAnalyzer()
    
    print("\nAnalyzing sample texts...\n")
    
    for text in sample_texts:
        result = analyzer.analyze(text)
        print(f"Text: {text[:60]}...")
        print(f"  Rating (1-5): {result['rating']}")
        print(f"  Sentiment Score: {result['sentiment_score']} ({result['label']})")
        print()
    
    # Show the conversion mapping
    print("=" * 60)
    print("Rating to Sentiment Score Mapping:")
    print("  Rating 1-2 → Sentiment Score: -1 (negative)")
    print("  Rating 3   → Sentiment Score:  0 (neutral)")
    print("  Rating 4-5 → Sentiment Score: +1 (positive)")
    print("=" * 60)
