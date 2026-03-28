"""
Article processor - Enriches news articles with AI-generated content and images
Ensures every article has complete content and proper images
"""

from .content_generator import generate_article_content
from .image_generator import generate_image_for_article


def process_article(article_data, force_regenerate=False):
    """
    Process and enrich a news article with complete content and images.
    
    Args:
        article_data: Dictionary containing article information
        force_regenerate: Force content regeneration even if content exists
    
    Returns:
        dict: Enhanced article with complete content and image
    """
    
    # Extract article info
    headline = article_data.get('title', '')
    source = article_data.get('source', {})
    if isinstance(source, dict):
        source_name = source.get('name', 'Unknown Source')
    else:
        source_name = str(source) if source else 'Unknown Source'
    
    summary = article_data.get('description', '') or article_data.get('summary', '')
    category = article_data.get('category', 'General')
    existing_content = article_data.get('content', '') or article_data.get('article_content', '')
    existing_image = article_data.get('urlToImage', '') or article_data.get('image_url', '')
    
    # 1. Check and generate article content if needed
    content_generated = False
    if force_regenerate or not existing_content or len(existing_content) < 500:
        print(f"[CONTENT] Generating full article content for: {headline[:50]}...")
        try:
            generated_content = generate_article_content(
                headline=headline,
                source=source_name,
                category=category,
                summary=summary
            )
            
            if generated_content and len(generated_content) > 500:
                article_data['content'] = generated_content
                article_data['article_content'] = generated_content
                content_generated = True
                print(f"[OK] Generated content: {len(generated_content)} chars (~{len(generated_content.split())} words)")
            else:
                print(f"[WARN] Generated content too short, keeping existing")
                article_data['content'] = existing_content or summary
                article_data['article_content'] = existing_content or summary
        except Exception as e:
            print(f"[ERROR] Content generation failed: {e}")
            # Keep existing or use summary as fallback
            article_data['content'] = existing_content or summary
            article_data['article_content'] = existing_content or summary
    else:
        # Use existing content
        article_data['content'] = existing_content
        article_data['article_content'] = existing_content
        print(f"[OK] Using existing content ({len(existing_content)} chars)")
    
    # 2. Check and generate image if needed
    image_generated = False
    if not existing_image or existing_image == '' or 'placeholder' in existing_image.lower():
        print(f"[IMAGE] Generating image for: {headline[:50]}...")
        try:
            generated_image = generate_image_for_article(headline, category)
            if generated_image:
                article_data['urlToImage'] = generated_image
                article_data['image_url'] = generated_image
                image_generated = True
                print(f"[OK] Generated image: {generated_image}")
            else:
                print(f"[WARN] Image generation returned None, using default")
                article_data['urlToImage'] = get_default_image(category)
                article_data['image_url'] = get_default_image(category)
        except Exception as e:
            print(f"[ERROR] Image generation failed: {e}")
            # Use default image
            article_data['urlToImage'] = get_default_image(category)
            article_data['image_url'] = get_default_image(category)
    else:
        # Use existing image
        article_data['urlToImage'] = existing_image
        article_data['image_url'] = existing_image
        print(f"[OK] Using existing image")
    
    # 3. Ensure all required fields are present
    article_data['headline'] = headline
    article_data['source'] = source_name
    
    # Remove any AI-related labels or metadata
    article_data = clean_article_metadata(article_data)
    
    print(f"[COMPLETE] Article processed - Content: {content_generated}, Image: {image_generated}")
    return article_data


def process_articles_batch(articles, force_regenerate=False):
    """
    Process multiple articles in batch.
    
    Args:
        articles: List of article dictionaries
        force_regenerate: Force content regeneration for all articles
    
    Returns:
        list: Enhanced articles
    """
    enhanced_articles = []
    total = len(articles)
    
    print(f"\n[BATCH] Processing {total} articles...")
    
    for idx, article in enumerate(articles, 1):
        try:
            print(f"\n[{idx}/{total}] Processing article...")
            enhanced_article = process_article(article, force_regenerate=force_regenerate)
            enhanced_articles.append(enhanced_article)
        except Exception as e:
            print(f"[ERROR] Failed to process article {idx}: {e}")
            # Add the original article even if processing fails
            enhanced_articles.append(article)
    
    print(f"\n[BATCH COMPLETE] Successfully processed {len(enhanced_articles)}/{total} articles")
    return enhanced_articles


def clean_article_metadata(article_data):
    """Remove AI-related labels and metadata from article"""
    
    # Fields that might contain AI labels
    text_fields = ['content', 'article_content', 'summary', 'description']
    
    for field in text_fields:
        if field in article_data and article_data[field]:
            content = str(article_data[field])
            
            # Remove common AI labels
            labels_to_remove = [
                'AI Generated',
                'AI-Generated',
                'Quick Read',
                'Summary',
                '[AI]',
                '(AI)',
                'This article was generated',
                'This content was generated',
                'Auto-generated',
                'Automatically generated',
            ]
            
            for label in labels_to_remove:
                content = content.replace(label, '')
                content = content.replace(label.lower(), '')
                content = content.replace(label.upper(), '')
            
            # Clean up extra whitespace
            content = ' '.join(content.split())
            article_data[field] = content
    
    # Remove metadata fields that shouldn't be exposed
    metadata_fields = [
        'ai_generated',
        'generated_by_ai',
        'content_generated',
        'image_generated',
        'processing_notes'
    ]
    
    for field in metadata_fields:
        article_data.pop(field, None)
    
    return article_data


def get_default_image(category='General'):
    """Get a default image URL for a category using reliable image sources"""
    import hashlib
    
    # Generate deterministic seed based on category for consistent images
    seed = abs(hash(category)) % 10000
    
    # Use Picsum Photos (reliable, free, no API key required)
    default_images = {
        'Technology': f'https://picsum.photos/seed/tech{seed}/1024/1024',
        'Business': f'https://picsum.photos/seed/business{seed}/1024/1024',
        'Sports': f'https://picsum.photos/seed/sports{seed}/1024/1024',
        'Entertainment': f'https://picsum.photos/seed/entertainment{seed}/1024/1024',
        'Health': f'https://picsum.photos/seed/health{seed}/1024/1024',
        'Science': f'https://picsum.photos/seed/science{seed}/1024/1024',
        'Environment': f'https://picsum.photos/seed/environment{seed}/1024/1024',
        'Politics': f'https://picsum.photos/seed/politics{seed}/1024/1024',
        'General': f'https://picsum.photos/seed/news{seed}/1024/1024',
    }
    
    return default_images.get(category, default_images['General'])


def validate_and_fix_image(article_data):
    """
    Validate article image and fix if missing/broken.
    Returns updated article_data with valid image.
    """
    import hashlib
    
    image_url = article_data.get('image_url') or article_data.get('urlToImage') or ''
    
    # Check if image is missing or invalid
    invalid_patterns = ['source.unsplash.com', 'placeholder', 'null', 'undefined', '']
    is_invalid = not image_url or any(pattern in image_url.lower() for pattern in invalid_patterns)
    
    if is_invalid:
        print(f"[IMAGE-FIX] Fixing missing image for: {article_data.get('title', '')[:50]}...")
        
        # Generate new image
        title = article_data.get('title', '')
        category = article_data.get('category', 'General')
        
        # Try DALL-E first, then fallback to Picsum
        try:
            from .image_generator import generate_image_for_article
            new_image = generate_image_for_article(title, category)
            if new_image:
                article_data['image_url'] = new_image
                article_data['urlToImage'] = new_image
                print(f"[IMAGE-FIX] ✅ Generated new image")
            else:
                # Use Picsum as ultimate fallback
                seed_text = f"{category}-{title[:30]}"
                seed = hashlib.md5(seed_text.encode()).hexdigest()[:8]
                article_data['image_url'] = f"https://picsum.photos/seed/{seed}/1024/1024"
                article_data['urlToImage'] = article_data['image_url']
                print(f"[IMAGE-FIX] ✅ Generated Picsum fallback")
        except Exception as e:
            print(f"[IMAGE-FIX] ⚠️ Error: {e}, using category default")
            article_data['image_url'] = get_default_image(category)
            article_data['urlToImage'] = article_data['image_url']
    
    return article_data


def ensure_article_quality(article_data):
    """
    Final quality check to ensure article meets minimum standards.
    
    Args:
        article_data: Article dictionary
    
    Returns:
        bool: True if article meets quality standards
    """
    required_fields = ['title', 'content', 'source', 'publish_time']
    
    # Check required fields
    for field in required_fields:
        if field not in article_data or not article_data[field]:
            print(f"[QUALITY] Article missing required field: {field}")
            return False
    
    # Check content length (should be at least 1000 characters for a complete article)
    content = article_data.get('content', '') or article_data.get('article_content', '')
    if len(content) < 1000:
        print(f"[QUALITY] Article content too short: {len(content)} chars")
        return False
    
    # Check headline length
    headline = article_data.get('title', '')
    if len(headline) < 10:
        print(f"[QUALITY] Headline too short: {headline}")
        return False
    
    print(f"[QUALITY] Article passed quality check")
    return True
