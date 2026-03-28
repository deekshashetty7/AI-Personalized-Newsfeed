"""
Semantic Search Module
Enhances search with NLP understanding for better query interpretation
"""

# Common synonyms mapping for news domain
SYNONYMS = {
    'car': ['automobile', 'vehicle', 'auto', 'motor'],
    'automobile': ['car', 'vehicle', 'auto', 'motor'],
    'vehicle': ['car', 'automobile', 'auto', 'motor'],
    'budget': ['finance', 'financial', 'fiscal', 'money', 'economic', 'funds', 'spending'],
    'finance': ['budget', 'financial', 'money', 'economic', 'funds', 'banking'],
    'financial': ['budget', 'finance', 'money', 'economic', 'fiscal'],
    'economy': ['economic', 'financial', 'finance', 'market', 'trade', 'commerce'],
    'economic': ['economy', 'financial', 'finance', 'market', 'commerce'],
    'slowdown': ['decline', 'decrease', 'drop', 'fall', 'downturn', 'slump'],
    'decline': ['slowdown', 'decrease', 'drop', 'fall', 'downturn', 'reduction'],
    'growth': ['increase', 'rise', 'expansion', 'boost', 'surge', 'upturn'],
    'increase': ['growth', 'rise', 'expansion', 'boost', 'surge'],
    'health': ['medical', 'healthcare', 'medicine', 'wellness', 'fitness'],
    'medical': ['health', 'healthcare', 'medicine', 'wellness', 'clinical'],
    'tech': ['technology', 'technological', 'digital', 'IT', 'computer'],
    'technology': ['tech', 'technological', 'digital', 'IT', 'innovation'],
    'AI': ['artificial intelligence', 'machine learning', 'ML', 'neural network', 'deep learning'],
    'sport': ['sports', 'game', 'match', 'competition', 'athletics'],
    'sports': ['sport', 'game', 'match', 'competition', 'athletics'],
    'politics': ['political', 'government', 'policy', 'election', 'governance'],
    'political': ['politics', 'government', 'policy', 'election', 'governance'],
    'environment': ['environmental', 'climate', 'ecology', 'nature', 'green'],
    'climate': ['environment', 'environmental', 'weather', 'global warming', 'temperature'],
    'business': ['corporate', 'company', 'enterprise', 'commercial', 'industry'],
    'corporate': ['business', 'company', 'enterprise', 'commercial', 'firm'],
    'stock': ['share', 'equity', 'market', 'trading', 'investment'],
    'market': ['stock', 'trading', 'exchange', 'commerce', 'business'],
    'election': ['vote', 'voting', 'poll', 'ballot', 'campaign'],
    'vote': ['election', 'voting', 'poll', 'ballot', 'referendum'],
    'war': ['conflict', 'battle', 'combat', 'military', 'warfare'],
    'conflict': ['war', 'battle', 'dispute', 'tension', 'clash'],
    'president': ['leader', 'chief', 'head', 'executive', 'premier'],
    'minister': ['official', 'secretary', 'leader', 'cabinet'],
    'crisis': ['emergency', 'disaster', 'catastrophe', 'trouble', 'problem'],
    'disaster': ['crisis', 'catastrophe', 'calamity', 'tragedy', 'emergency'],
}

# Country and location mappings
LOCATIONS = {
    'india': ['indian', 'delhi', 'mumbai', 'bangalore', 'hindustan'],
    'indian': ['india', 'delhi', 'mumbai', 'bangalore'],
    'us': ['usa', 'united states', 'america', 'american'],
    'usa': ['us', 'united states', 'america', 'american'],
    'america': ['us', 'usa', 'united states', 'american'],
    'american': ['america', 'us', 'usa', 'united states'],
    'uk': ['britain', 'british', 'united kingdom', 'england'],
    'britain': ['uk', 'british', 'united kingdom', 'england'],
    'china': ['chinese', 'beijing', 'shanghai'],
    'chinese': ['china', 'beijing', 'shanghai'],
}

# Action words and their contexts
ACTION_CONTEXTS = {
    'news': ['article', 'report', 'story', 'update'],
    'latest': ['recent', 'new', 'current', 'today'],
    'recent': ['latest', 'new', 'current', 'today'],
    'breaking': ['urgent', 'latest', 'important', 'critical'],
}

def expand_query_with_synonyms(query):
    """
    Expand search query with synonyms to catch related terms
    
    Example:
        "India economy slowdown news" -> 
        includes: economy, economic, finance, financial, slowdown, decline, decrease
    """
    query_lower = query.lower()
    words = query_lower.split()
    expanded_terms = set(words)  # Start with original words
    
    # Add synonyms for each word
    for word in words:
        word_clean = word.strip('.,!?;:')
        if word_clean in SYNONYMS:
            expanded_terms.update(SYNONYMS[word_clean])
        if word_clean in LOCATIONS:
            expanded_terms.update(LOCATIONS[word_clean])
        if word_clean in ACTION_CONTEXTS:
            expanded_terms.update(ACTION_CONTEXTS[word_clean])
    
    return list(expanded_terms)


def extract_intent(query):
    """
    Extract the intent/meaning from the search query
    
    Returns:
        dict with location, topic, sentiment, timeframe
    """
    query_lower = query.lower()
    words = query_lower.split()
    
    intent = {
        'location': None,
        'topic': [],
        'sentiment': 'neutral',
        'timeframe': None
    }
    
    # Extract location
    for word in words:
        word_clean = word.strip('.,!?;:')
        if word_clean in LOCATIONS or word_clean in ['india', 'us', 'usa', 'uk', 'china']:
            intent['location'] = word_clean
            break
    
    # Extract topic/category hints
    category_keywords = {
        'technology': ['tech', 'technology', 'ai', 'digital', 'software', 'computer'],
        'business': ['business', 'corporate', 'company', 'market', 'stock', 'economy'],
        'sports': ['sport', 'sports', 'game', 'match', 'player', 'team'],
        'health': ['health', 'medical', 'disease', 'medicine', 'doctor', 'hospital'],
        'politics': ['politics', 'political', 'government', 'election', 'minister'],
        'environment': ['environment', 'climate', 'pollution', 'ecology', 'nature'],
        'entertainment': ['entertainment', 'movie', 'film', 'music', 'celebrity'],
        'science': ['science', 'research', 'study', 'discovery', 'experiment']
    }
    
    for category, keywords in category_keywords.items():
        for word in words:
            if word.strip('.,!?;:') in keywords:
                intent['topic'].append(category)
                break
    
    # Extract sentiment
    positive_words = ['growth', 'success', 'achievement', 'victory', 'rise', 'boost']
    negative_words = ['slowdown', 'decline', 'crisis', 'fall', 'loss', 'failure']
    
    for word in words:
        word_clean = word.strip('.,!?;:')
        if word_clean in positive_words:
            intent['sentiment'] = 'positive'
        elif word_clean in negative_words:
            intent['sentiment'] = 'negative'
    
    # Extract timeframe
    time_words = ['latest', 'recent', 'today', 'yesterday', 'breaking', 'current', 'new']
    for word in words:
        if word.strip('.,!?;:') in time_words:
            intent['timeframe'] = 'recent'
            break
    
    return intent


def build_semantic_query(search_text):
    """
    Build an enhanced MongoDB query using semantic understanding
    Search only in headlines/titles for better precision
    
    Args:
        search_text: Original search query from user
        
    Returns:
        dict: MongoDB query with semantic enhancements
    """
    if not search_text:
        return {}
    
    # Split search text into individual keywords
    keywords = [word.strip('.,!?;:').lower() for word in search_text.split() if word.strip()]
    
    # Get expanded terms with synonyms
    expanded_terms = expand_query_with_synonyms(search_text)
    
    # Extract intent
    intent = extract_intent(search_text)
    
    # Build MongoDB $or query for flexible matching (TITLE ONLY)
    conditions = []
    
    # Add exact phrase matching in title (highest priority)
    conditions.append({'title': {'$regex': search_text, '$options': 'i'}})
    
    # Add individual keyword matching in title only
    for keyword in keywords:
        if len(keyword) >= 2:  # Only search keywords with 2+ characters
            conditions.append({'title': {'$regex': keyword, '$options': 'i'}})
    
    # Add expanded terms (synonyms) matching in title only
    for term in expanded_terms:
        if term not in keywords:  # Avoid duplicate conditions
            conditions.append({'title': {'$regex': term, '$options': 'i'}})
    
    # Add category matching if topic detected
    if intent['topic']:
        for topic in intent['topic']:
            conditions.append({'category': {'$regex': topic, '$options': 'i'}})
    
    # Build final query
    if conditions:
        return {'$or': conditions}
    else:
        # Fallback to basic search in title only
        return {'title': {'$regex': search_text, '$options': 'i'}}


def rank_results(articles, search_text):
    """
    Rank search results by relevance using semantic scoring
    Focuses only on title/headline matching for precision
    
    Args:
        articles: List of article dicts from database
        search_text: Original search query
        
    Returns:
        List of articles sorted by relevance score
    """
    if not search_text or not articles:
        return articles
    
    query_lower = search_text.lower()
    keywords = [word.strip('.,!?;:').lower() for word in search_text.split() if word.strip()]
    expanded_terms = expand_query_with_synonyms(search_text)
    intent = extract_intent(search_text)
    
    # Score each article based on TITLE ONLY
    for article in articles:
        score = 0
        title = article.get('title', '').lower()
        category = article.get('category', '').lower()
        
        # Exact phrase match in title (highest score)
        if query_lower in title:
            score += 200
        
        # Count how many keywords appear in title
        keywords_in_title = sum(1 for kw in keywords if kw in title)
        
        # Bonus for multiple keyword matches (indicates higher relevance)
        if keywords_in_title > 0:
            score += keywords_in_title * 30  # 30 points per keyword in title
        
        # Bonus if ALL keywords are present in title (very high relevance)
        if len(keywords) > 1:
            all_in_title = all(kw in title for kw in keywords)
            if all_in_title:
                score += 150
        
        # Individual word matches in title
        for word in keywords:
            word_clean = word.strip('.,!?;:')
            if word_clean in title:
                score += 20
        
        # Synonym matches in title
        for term in expanded_terms:
            if term not in keywords:  # Avoid double-counting
                if term in title:
                    score += 15
        
        # Category/topic match
        if intent['topic']:
            for topic in intent['topic']:
                if topic.lower() == category:
                    score += 50
                elif topic.lower() in category:
                    score += 25
        
        # Location match in title
        if intent['location']:
            if intent['location'] in title:
                score += 30
        
        article['_relevance_score'] = score
    
    # Sort by relevance score (highest first)
    articles.sort(key=lambda x: x.get('_relevance_score', 0), reverse=True)
    
    # Log top results for debugging
    print(f"🎯 Top 5 headline matches for '{search_text}':")
    for i, article in enumerate(articles[:5], 1):
        score = article.get('_relevance_score', 0)
        title = article.get('title', '')[:70]
        print(f"   {i}. [{score} pts] {title}")
    
    # Remove temporary score field
    for article in articles:
        article.pop('_relevance_score', None)
    
    return articles
