"""
Advanced AI Personalization Engine for "AI Picks" Section
Implements comprehensive user profiling, content analysis, and intelligent matching
"""

from datetime import datetime, timedelta
from collections import defaultdict
import math


def apply_time_decay(preference_score, last_interaction, decay_days=30):
    """
    Apply time-based decay to old preferences
    Preferences lose weight if not reinforced
    
    Args:
        preference_score: Current preference score (0-1)
        last_interaction: DateTime of last interaction
        decay_days: Days after which preferences start decaying
    
    Returns:
        Decayed preference score
    """
    if not last_interaction:
        return preference_score
    
    days_since_interaction = (datetime.now(last_interaction.tzinfo) - last_interaction).days
    
    if days_since_interaction <= decay_days:
        return preference_score
    
    # Exponential decay after decay_days
    decay_factor = math.exp(-(days_since_interaction - decay_days) / 30.0)
    return preference_score * (0.3 + 0.7 * decay_factor)  # Minimum 30% retention


def get_user_interest_profile(user_preferences, apply_decay=True):
    """
    Build comprehensive user interest profile from preferences
    
    Returns:
        Dict mapping category -> weighted score (with optional decay)
    """
    profile = {}
    
    for pref in user_preferences:
        score = pref.preference_score
        
        # Apply time-based decay to reduce weight of old interests
        if apply_decay:
            score = apply_time_decay(score, pref.last_interaction)
        
        # Weight by interaction frequency (more interactions = stronger signal)
        frequency_weight = min(1.0, math.log(pref.interaction_count + 1) / 5.0)
        
        # Weight by total engagement time
        time_weight = min(1.0, math.log(pref.total_dwell_time + 1) / 10.0)
        
        # Combined weighted score
        final_score = score * (0.5 + frequency_weight * 0.3 + time_weight * 0.2)
        
        profile[pref.category] = final_score
    
    return profile


def analyze_article_profile(article):
    """
    Create content profile for an article
    
    Returns:
        Dict with article features for matching
    """
    return {
        'category': article.get('category', 'General'),
        'sentiment': article.get('sentiment_score', 0.0),
        'recency_hours': (datetime.now() - datetime.fromisoformat(
            str(article.get('publish_time', datetime.now())).replace('Z', '+00:00')
        )).total_seconds() / 3600 if article.get('publish_time') else 24,
        'has_image': bool(article.get('image_url')),
        'title': article.get('title', ''),
        'keywords': extract_keywords(article.get('title', '') + ' ' + article.get('summary', ''))
    }


def extract_keywords(text):
    """Extract important keywords from text"""
    # Simple keyword extraction (can be enhanced with NLP)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    words = text.lower().split()
    keywords = [w for w in words if len(w) > 3 and w not in stop_words]
    return keywords[:10]  # Top 10 keywords


def calculate_match_score(user_profile, article_profile, recent_interactions):
    """
    AI Matching Engine: Calculate how well an article matches user interests
    
    Args:
        user_profile: Dict of category -> preference score
        article_profile: Dict of article features
        recent_interactions: List of recent article IDs user interacted with
    
    Returns:
        Float score (0-100) indicating match quality
    """
    score = 0.0
    
    # 1. Category Match (45% weight) - Core personalization (increased from 40%)
    category = article_profile['category']
    category_score = user_profile.get(category, 0.25)  # Lower default for exploration
    
    # Apply non-linear scaling for strong preferences
    if category_score > 0.7:
        category_score = min(1.0, category_score * 1.15)  # Boost strong interests
    elif category_score < 0.3:
        category_score = max(0.1, category_score * 0.8)  # Reduce weak interests
    
    score += category_score * 45
    
    # 2. Recency Boost (22% weight) - Fresh content is critical (increased from 20%)
    recency_hours = article_profile['recency_hours']
    if recency_hours < 1:
        recency_score = 1.0  # Breaking news
    elif recency_hours < 3:
        recency_score = 0.95  # Very fresh
    elif recency_hours < 6:
        recency_score = 0.85
    elif recency_hours < 12:
        recency_score = 0.7
    elif recency_hours < 24:
        recency_score = 0.5
    elif recency_hours < 48:
        recency_score = 0.3
    else:
        recency_score = max(0.05, 1.0 - recency_hours / 240)  # Decay over 10 days
    score += recency_score * 22
    
    # 3. Visual Content Boost (13% weight) - Images critical for engagement
    if article_profile['has_image']:
        score += 13
    else:
        score += 2  # Small baseline for text-only
    
    # 4. Diversity Boost (15% weight) - Reward novel content
    article_id = article_profile.get('_id')
    if article_id and article_id not in recent_interactions[-30:]:
        score += 15  # Full novelty bonus
    elif article_id and article_id not in recent_interactions[-10:]:
        score += 7  # Partial bonus if seen a while ago
    # Penalize recently seen content
    elif article_id and article_id in recent_interactions[-5:]:
        score -= 10  # Significant penalty for very recent
    
    # 5. Sentiment & Quality (5% weight) - Prefer balanced, quality content
    sentiment = article_profile['sentiment']
    if -0.3 <= sentiment <= 0.3:  # Balanced articles
        score += 5
    elif sentiment < -0.7:  # Breaking/critical news
        score += 4
    elif sentiment > 0.7:  # Very positive
        score += 3
    
    return min(100.0, max(0.0, score))


def generate_personalized_feed(user_preferences, articles, recent_interactions, top_n=30):
    """
    Main AI Engine: Generate personalized "For You" feed
    
    Implements:
    - Interest-based filtering and ranking
    - Exploration/exploitation balance (90/10 split)
    - Time decay for old preferences
    - Diversity to prevent filter bubbles
    - Smart fallback for new users
    
    Args:
        user_preferences: QuerySet of UserPreference objects
        articles: List of article dicts
        recent_interactions: List of recent article IDs
        top_n: Number of articles to return
    
    Returns:
        List of article IDs ranked by relevance
    """
    # Build user interest profile with time decay
    user_profile = get_user_interest_profile(user_preferences, apply_decay=True)
    
    # Filter out recently interacted articles (no duplicates in last 50 interactions)
    filtered_articles = [
        article for article in articles 
        if article.get('_id') not in recent_interactions[:50]
    ]
    
    # If too few articles remain, use all articles
    if len(filtered_articles) < top_n:
        filtered_articles = articles
    
    if not user_profile or len(user_profile) == 0:
        # NEW USER FALLBACK: Show trending, recent content with variety
        scored_articles = []
        
        for article in filtered_articles:
            profile = analyze_article_profile(article)
            
            # Score based on multiple factors for new users
            score = 0
            
            # Recency (40%)
            if profile['recency_hours'] < 6:
                score += 40
            elif profile['recency_hours'] < 24:
                score += 30
            else:
                score += 10
            
            # Visual appeal (30%)
            if profile['has_image']:
                score += 30
            
            # Category diversity (30%) - spread across categories
            # This ensures new users see variety
            category_bonus = hash(profile['category']) % 30
            score += category_bonus
            
            scored_articles.append((article.get('_id'), score))
    else:
        # EXPERIENCED USER: Personalized AI matching
        scored_articles = []
        
        for article in filtered_articles:
            article_profile = analyze_article_profile(article)
            article_profile['_id'] = article.get('_id')
            
            # Calculate AI match score
            match_score = calculate_match_score(user_profile, article_profile, recent_interactions)
            
            scored_articles.append((article.get('_id'), match_score))
        
        # Exploration/Exploitation: 90% personalized, 10% diverse
        scored_articles.sort(key=lambda x: x[1], reverse=True)
        
        # Take top 90% from personalized ranking
        exploitation_count = int(top_n * 0.9)
        exploitation_articles = scored_articles[:exploitation_count]
        
        # Take 10% from lower-ranked diverse content (exploration)
        if len(scored_articles) > exploitation_count + 10:
            exploration_pool = scored_articles[exploitation_count:exploitation_count + 50]
            # Randomly sample for serendipity
            import random
            exploration_articles = random.sample(
                exploration_pool, 
                min(top_n - exploitation_count, len(exploration_pool))
            )
        else:
            exploration_articles = scored_articles[exploitation_count:top_n]
        
        # Combine: Personalized first, then diverse content
        final_ids = [aid for aid, score in exploitation_articles]
        final_ids.extend([aid for aid, score in exploration_articles])
        
        return final_ids[:top_n]
    
    # Sort by score and return top N (for new users)
    scored_articles.sort(key=lambda x: x[1], reverse=True)
    return [article_id for article_id, score in scored_articles[:top_n]]


def update_user_profile_realtime(user_id, article_category, action, dwell_time=0):
    """
    Real-time profile update when user interacts with content
    This is called automatically after every interaction
    """
    # This is now handled in views.py interaction handler
    # Keeping this function for potential future enhancements
    pass
