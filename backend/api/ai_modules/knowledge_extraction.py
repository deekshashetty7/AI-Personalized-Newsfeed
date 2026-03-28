"""
Knowledge Box AI Module
Automatically detects topics, extracts entities, and organizes user's reading knowledge
"""

import re
from collections import Counter
from datetime import datetime, timedelta


# Common stop words to filter out
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
    'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does',
    'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
    'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who',
    'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
    'very', 's', 't', 'just', 'now', 'says', 'said', 'new', 'year', 'years'
}


def extract_topics_from_article(article_data):
    """
    Extract main topics from article using category and keywords
    
    Returns:
        list: Main topics identified
    """
    topics = []
    
    # Primary topic from category
    category = article_data.get('category', 'General')
    if category and category != 'General':
        topics.append(category)
    
    # Extract from title keywords
    title = article_data.get('title', '')
    keywords = extract_keywords(title)
    
    # Identify multi-word topics
    title_lower = title.lower()
    
    # Technology topics
    tech_topics = [
        'artificial intelligence', 'machine learning', 'ai', 'blockchain', 'cryptocurrency',
        'bitcoin', 'ethereum', 'cloud computing', 'cybersecurity', 'quantum computing',
        'virtual reality', 'augmented reality', 'robotics', 'automation', '5g'
    ]
    for topic in tech_topics:
        if topic in title_lower:
            topics.append(topic.title())
    
    # Political/Business entities
    entities = extract_entities(title)
    topics.extend(entities[:2])  # Top 2 entities
    
    # Add significant keywords as topics
    for keyword in keywords[:2]:
        if len(keyword) > 4:
            topics.append(keyword.title())
    
    # Remove duplicates and return
    return list(dict.fromkeys(topics))[:3]  # Top 3 topics


def extract_keywords(text):
    """
    Extract important keywords from text
    """
    if not text:
        return []
    
    # Clean and tokenize
    text = text.lower()
    words = re.findall(r'\b[a-z]{4,}\b', text)
    
    # Filter stop words
    keywords = [w for w in words if w not in STOP_WORDS]
    
    # Count frequency
    word_freq = Counter(keywords)
    
    # Return top keywords
    return [word for word, count in word_freq.most_common(10)]


def extract_entities(text):
    """
    Extract named entities (people, organizations, places)
    Simple implementation - can be enhanced with NLP libraries
    """
    if not text:
        return []
    
    entities = []
    
    # Capitalized words (potential entities)
    words = text.split()
    for i, word in enumerate(words):
        # Skip first word and common words
        if i > 0 and word[0].isupper() and word.lower() not in STOP_WORDS:
            # Check for multi-word entities
            if i + 1 < len(words) and words[i + 1][0].isupper():
                entities.append(f"{word} {words[i + 1]}")
            else:
                entities.append(word)
    
    # Known organizations/companies
    companies = [
        'Google', 'Apple', 'Microsoft', 'Amazon', 'Facebook', 'Meta', 'Tesla',
        'OpenAI', 'Netflix', 'Twitter', 'SpaceX', 'NASA', 'WHO', 'UN', 'EU',
        'Congress', 'Senate', 'House', 'Supreme Court', 'White House'
    ]
    
    for company in companies:
        if company.lower() in text.lower():
            entities.append(company)
    
    # Remove duplicates
    return list(dict.fromkeys(entities))[:5]


def extract_subtopics(article_data):
    """
    Extract subtopics from article content
    """
    title = article_data.get('title', '')
    summary = article_data.get('summary', '')
    
    combined_text = f"{title} {summary}".lower()
    
    subtopics = []
    
    # Technology subtopics
    tech_patterns = {
        'AI': ['gpt', 'chatgpt', 'generative ai', 'llm', 'neural network'],
        'Electric Vehicles': ['ev', 'electric car', 'battery', 'charging'],
        'Social Media': ['facebook', 'instagram', 'tiktok', 'twitter', 'social platform'],
        'Climate': ['climate change', 'global warming', 'carbon', 'emissions', 'renewable'],
        'Health': ['covid', 'vaccine', 'pandemic', 'disease', 'medical'],
        'Finance': ['stock', 'market', 'investment', 'crypto', 'trading'],
        'Politics': ['election', 'vote', 'government', 'president', 'policy'],
        'Sports': ['game', 'match', 'championship', 'player', 'team']
    }
    
    for subtopic, patterns in tech_patterns.items():
        for pattern in patterns:
            if pattern in combined_text:
                subtopics.append(subtopic)
                break
    
    return list(set(subtopics))[:5]


def calculate_importance_score(article_count, total_time, recency_days):
    """
    Calculate importance score for a topic
    
    Factors:
    - Frequency (how many articles read)
    - Time spent (total engagement)
    - Recency (how recently accessed)
    
    Returns:
        float: Score between 0 and 1
    """
    # Frequency score (0-0.4)
    freq_score = min(0.4, article_count * 0.05)
    
    # Engagement score (0-0.4)
    minutes_spent = total_time / 60
    engagement_score = min(0.4, minutes_spent * 0.01)
    
    # Recency score (0-0.2)
    if recency_days == 0:
        recency_score = 0.2
    elif recency_days <= 7:
        recency_score = 0.15
    elif recency_days <= 30:
        recency_score = 0.10
    else:
        recency_score = 0.05
    
    return freq_score + engagement_score + recency_score


def update_knowledge_box(user_id, article, dwell_time):
    """
    Update user's knowledge box after reading an article
    
    This is called automatically when user reads an article
    """
    from api.models import KnowledgeBox
    
    # Extract information
    topics = extract_topics_from_article(article)
    entities = extract_entities(article.get('title', ''))
    subtopics = extract_subtopics(article)
    
    article_id = str(article.get('_id', ''))
    
    # Update or create knowledge entries for each topic
    for topic in topics:
        knowledge, created = KnowledgeBox.objects.get_or_create(
            user_id=user_id,
            topic=topic,
            defaults={
                'article_count': 0,
                'total_time_spent': 0,
                'importance_score': 0.0,
                'subtopics': [],
                'key_entities': [],
                'article_ids': []
            }
        )
        
        # Update metrics
        knowledge.article_count += 1
        knowledge.total_time_spent += dwell_time
        
        # Add article ID if not already present
        if article_id not in knowledge.article_ids:
            knowledge.article_ids.append(article_id)
            # Keep only last 20 articles
            if len(knowledge.article_ids) > 20:
                knowledge.article_ids = knowledge.article_ids[-20:]
        
        # Merge new entities and subtopics
        for entity in entities:
            if entity not in knowledge.key_entities:
                knowledge.key_entities.append(entity)
        knowledge.key_entities = knowledge.key_entities[:10]  # Keep top 10
        
        for subtopic in subtopics:
            if subtopic not in knowledge.subtopics:
                knowledge.subtopics.append(subtopic)
        knowledge.subtopics = knowledge.subtopics[:8]  # Keep top 8
        
        # Recalculate importance score
        recency_days = (datetime.now() - knowledge.last_read.replace(tzinfo=None)).days
        knowledge.importance_score = calculate_importance_score(
            knowledge.article_count,
            knowledge.total_time_spent,
            recency_days
        )
        
        knowledge.save()


def fade_old_knowledge(user_id, days_threshold=90):
    """
    Fade importance of old, unused topics
    Called periodically to clean up knowledge box
    """
    from api.models import KnowledgeBox
    
    cutoff_date = datetime.now() - timedelta(days=days_threshold)
    
    old_knowledge = KnowledgeBox.objects.filter(
        user_id=user_id,
        last_read__lt=cutoff_date
    )
    
    for item in old_knowledge:
        # Reduce importance by 50%
        item.importance_score *= 0.5
        
        # Delete if importance too low
        if item.importance_score < 0.1:
            item.delete()
        else:
            item.save()


def get_knowledge_summary(user_id):
    """
    Get organized summary of user's knowledge box
    
    Returns:
        dict: Organized knowledge with topics, subtopics, and timelines
    """
    from api.models import KnowledgeBox
    
    knowledge_items = KnowledgeBox.objects.filter(user_id=user_id).order_by('-importance_score')[:20]
    
    # Organize by topic hierarchy
    organized = []
    
    for item in knowledge_items:
        organized.append({
            'topic': item.topic,
            'article_count': item.article_count,
            'total_time_spent': item.total_time_spent,
            'importance_score': item.importance_score,
            'subtopics': item.subtopics,
            'key_entities': item.key_entities,
            'last_read': item.last_read.isoformat(),
            'first_read': item.first_read.isoformat()
        })
    
    return organized
