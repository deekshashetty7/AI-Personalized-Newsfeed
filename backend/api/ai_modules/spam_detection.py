"""
Spam Detection Module
Uses keyword-based detection and pattern matching
Detects fake, clickbait, and spam articles
"""

import re
from collections import Counter


class SpamDetector:
    def __init__(self):
        self.model_version = "rule_based_v1.0"
        
        # Spam indicators
        self.spam_keywords = [
            'click here', 'buy now', 'limited time', 'act now', 'free money',
            'earn cash', 'work from home', 'make money fast', 'risk free',
            'guaranteed', 'special promotion', 'order now', 'call now',
            'you won', 'congratulations', 'claim your', 'click below'
        ]
        
        # Clickbait patterns
        self.clickbait_patterns = [
            r'you won\'t believe',
            r'this one trick',
            r'doctors hate',
            r'number \d+ will shock you',
            r'what happens next',
            r'the reason why',
            r'\d+ reasons why',
            r'this is why',
            r'mind blown',
            r'gone wrong'
        ]
    
    def detect(self, text, title=""):
        """
        Detect if content is spam
        Returns: (is_spam: bool, spam_score: float, reasons: list)
        """
        if not text and not title:
            return False, 0.0, []
        
        full_text = f"{title} {text}".lower()
        spam_score = 0.0
        reasons = []
        
        # Check spam keywords
        keyword_count = sum(1 for keyword in self.spam_keywords if keyword in full_text)
        if keyword_count > 0:
            spam_score += keyword_count * 0.2
            reasons.append(f"Contains {keyword_count} spam keywords")
        
        # Check clickbait patterns
        clickbait_count = sum(1 for pattern in self.clickbait_patterns 
                             if re.search(pattern, full_text))
        if clickbait_count > 0:
            spam_score += clickbait_count * 0.25
            reasons.append(f"Contains {clickbait_count} clickbait patterns")
        
        # Check excessive capitalization
        if title:
            cap_ratio = sum(1 for c in title if c.isupper()) / max(len(title), 1)
            if cap_ratio > 0.5:
                spam_score += 0.3
                reasons.append("Excessive capitalization")
        
        # Check excessive punctuation
        punct_count = len(re.findall(r'[!?]{2,}', full_text))
        if punct_count > 0:
            spam_score += punct_count * 0.15
            reasons.append("Excessive punctuation")
        
        # Check for too many numbers (common in spam)
        number_count = len(re.findall(r'\d+', full_text))
        if number_count > 10:
            spam_score += 0.2
            reasons.append("Excessive numbers")
        
        # Normalize spam score to 0-1
        spam_score = min(spam_score, 1.0)
        
        # Consider spam if score > 0.5
        is_spam = spam_score > 0.5
        
        return is_spam, round(spam_score, 3), reasons
    
    def detect_article(self, article_data):
        """Detect spam in article data"""
        title = article_data.get('title', '')
        content = article_data.get('description', '') + ' ' + article_data.get('content', '')
        return self.detect(content, title)


# Global instance
spam_detector = SpamDetector()


def detect_spam(text, title=""):
    """Convenience function for spam detection"""
    is_spam, score, reasons = spam_detector.detect(text, title)
    return is_spam


def detect_article_spam(article_data):
    """Detect spam in article"""
    return spam_detector.detect_article(article_data)
