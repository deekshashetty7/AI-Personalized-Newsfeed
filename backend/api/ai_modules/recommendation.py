"""
Recommendation Engine
Hybrid recommendation system combining:
1. Content-based filtering (TF-IDF similarity)
2. Collaborative filtering (user interaction patterns)
3. Sentiment-weighted scoring
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime, timedelta


class RecommendationEngine:
    def __init__(self):
        self.model_version = "hybrid_v1.0"
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    def get_content_based_recommendations(self, user_interests, articles, top_n=10):
        """
        Content-based recommendations based on user interests
        """
        if not articles:
            return []
        
        # Create article texts for TF-IDF
        article_texts = []
        article_ids = []
        
        for article in articles:
            text = f"{article.get('title', '')} {article.get('category', '')} {article.get('summary', '')}"
            article_texts.append(text)
            article_ids.append(article.get('_id'))
        
        # User interest text
        user_text = ' '.join(user_interests) if user_interests else 'general news'
        
        # Fit TF-IDF and compute similarities
        try:
            all_texts = [user_text] + article_texts
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
            
            # Compute cosine similarity between user and articles
            user_vector = tfidf_matrix[0:1]
            article_vectors = tfidf_matrix[1:]
            
            similarities = cosine_similarity(user_vector, article_vectors)[0]
            
            # Apply sentiment preference boost
            sentiment_adjusted_scores = []
            for idx, sim_score in enumerate(similarities):
                article_sentiment = article_sentiments[idx]
                # Boost score if article sentiment matches user preference
                sentiment_boost = 1.0 - abs(article_sentiment - user_sentiment_pref) * 0.3
                adjusted_score = sim_score * sentiment_boost
                sentiment_adjusted_scores.append(adjusted_score)
            
            # Get top N articles
            top_indices = np.argsort(sentiment_adjusted_scores)[-top_n:][::-1]
            
            recommendations = []
            for idx in top_indices:
                recommendations.append({
                    'article_id': article_ids[idx],
                    'score': float(sentiment_adjusted_scores[idx]),
                    'reason': 'content_match',
                    'sentiment_match': 1.0 - abs(article_sentiments[idx] - user_sentiment_pref)
                })
            
            return recommendations
        
        except Exception as e:
            print(f"Content-based recommendation error: {e}")
            # Fallback: return recent articles
            return [{'article_id': aid, 'score': 0.5, 'reason': 'recent'} 
                   for aid in article_ids[:top_n]]
    
    def get_collaborative_recommendations(self, user_id, interactions, articles, top_n=10):
        """
        Collaborative filtering based on user interactions
        Find similar users and recommend their liked articles
        """
        if not interactions:
            return []
        
        # Build user-article interaction matrix
        user_interactions = defaultdict(dict)
        
        for interaction in interactions:
            uid = interaction.get('user_id')
            aid = interaction.get('article_id')
            action = interaction.get('action')
            
            # Score different actions
            score = 0
            if action == 'like':
                score = 1.0
            elif action == 'save':
                score = 0.8
            elif action == 'share':
                score = 0.6
            elif action == 'read':
                score = 0.3
            elif action == 'dislike':
                score = -1.0
            
            if aid not in user_interactions[uid]:
                user_interactions[uid][aid] = 0
            user_interactions[uid][aid] += score
        
        # Find similar users (users who interacted with same articles)
        if user_id not in user_interactions:
            return []
        
        user_articles = set(user_interactions[user_id].keys())
        similar_users = []
        
        for uid, interactions_dict in user_interactions.items():
            if uid == user_id:
                continue
            
            other_articles = set(interactions_dict.keys())
            overlap = len(user_articles & other_articles)
            
            if overlap > 0:
                similarity = overlap / max(len(user_articles), len(other_articles))
                similar_users.append((uid, similarity))
        
        # Sort by similarity
        similar_users.sort(key=lambda x: x[1], reverse=True)
        
        # Collect articles from similar users
        article_scores = defaultdict(float)
        
        for uid, similarity in similar_users[:5]:  # Top 5 similar users
            for aid, score in user_interactions[uid].items():
                if aid not in user_articles and score > 0:
                    article_scores[aid] += score * similarity
        
        # Sort and return top N
        sorted_articles = sorted(article_scores.items(), key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for aid, score in sorted_articles[:top_n]:
            recommendations.append({
                'article_id': aid,
                'score': float(score),
                'reason': 'collaborative'
            })
        
        return recommendations
    
    def get_trending_recommendations(self, interactions, articles, top_n=10, hours=24):
        """
        Recommend trending articles based on recent interactions
        """
        if not interactions:
            return []
        
        # Count recent interactions
        cutoff_time = datetime.now() - timedelta(hours=hours)
        article_engagement = Counter()
        
        for interaction in interactions:
            timestamp = interaction.get('timestamp')
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            if timestamp > cutoff_time:
                aid = interaction.get('article_id')
                action = interaction.get('action')
                
                # Weight different actions
                weight = 1
                if action == 'like':
                    weight = 3
                elif action == 'share':
                    weight = 4
                elif action == 'save':
                    weight = 2
                
                article_engagement[aid] += weight
        
        # Get top trending articles
        trending = article_engagement.most_common(top_n)
        
        recommendations = []
        for aid, engagement in trending:
            recommendations.append({
                'article_id': aid,
                'score': float(engagement) / 10.0,  # Normalize
                'reason': 'trending'
            })
        
        return recommendations
    
    def get_hybrid_recommendations(self, user_id, user_interests, interactions, articles, top_n=20):
        """
        Hybrid recommendation combining multiple strategies with sentiment awareness
        """
        all_recommendations = {}
        
        # Learn user's sentiment preference from interactions
        user_sentiment_pref = self.get_user_sentiment_preference(interactions)
        
        # Get content-based recommendations (weight: 0.4) with sentiment boost
        content_recs = self.get_content_based_recommendations(
            user_interests, articles, top_n, user_sentiment_pref
        )
        for rec in content_recs:
            aid = rec['article_id']
            if aid not in all_recommendations:
                all_recommendations[aid] = 0
            all_recommendations[aid] += rec['score'] * 0.4
        
        # Get collaborative recommendations (weight: 0.35)
        collab_recs = self.get_collaborative_recommendations(user_id, interactions, articles, top_n)
        for rec in collab_recs:
            aid = rec['article_id']
            if aid not in all_recommendations:
                all_recommendations[aid] = 0
            all_recommendations[aid] += rec['score'] * 0.35
        
        # Get trending recommendations (weight: 0.25)
        trending_recs = self.get_trending_recommendations(interactions, articles, top_n)
        for rec in trending_recs:
            aid = rec['article_id']
            if aid not in all_recommendations:
                all_recommendations[aid] = 0
            all_recommendations[aid] += rec['score'] * 0.25
        
        # Sort by combined score
        sorted_recs = sorted(all_recommendations.items(), key=lambda x: x[1], reverse=True)
        
        # Return top N article IDs
        return [aid for aid, score in sorted_recs[:top_n]]


# Global instance
recommendation_engine = RecommendationEngine()


def generate_recommendations(user_id, user_interests, interactions, articles, top_n=20):
    """Generate hybrid recommendations for a user"""
    return recommendation_engine.get_hybrid_recommendations(
        user_id, user_interests, interactions, articles, top_n
    )
