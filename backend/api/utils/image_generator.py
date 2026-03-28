"""
Image generation utility for news articles using OpenAI DALL-E
"""
import os
import base64
import requests
import hashlib
from urllib.parse import quote
from django.conf import settings

try:
    from openai import OpenAI
    OPENAI_CLIENT_AVAILABLE = True
except ImportError:
    OPENAI_CLIENT_AVAILABLE = False


def generate_image_for_article(title, category='news'):
    """
    Generate images for articles using OpenAI DALL-E based on title and category.
    Falls back to Unsplash if OpenAI fails.
    """
    
    # Try OpenAI DALL-E first
    openai_image = generate_image_with_openai(title, category)
    if openai_image:
        return openai_image
    
    # Fallback to Unsplash
    print(f"[FALLBACK] Using Unsplash for: {title[:50]}...")
    return generate_image_with_unsplash(title, category)


def generate_image_with_openai(title, category):
    """
    Generate image using OpenAI DALL-E based on article headline.
    Creates a professional news-related image.
    """
    openai_api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
    
    if not openai_api_key:
        print("[WARN] OpenAI API key not found, skipping image generation")
        return None
    
    if not OPENAI_CLIENT_AVAILABLE:
        print("[WARN] OpenAI client not available, skipping image generation")
        return None
    
    try:
        prompt = create_image_prompt(title, category)
        print(f"[DALL-E] Generating image for: {title[:50]}...")
        
        # Use new OpenAI client with minimal configuration to avoid conflicts
        client = OpenAI(api_key=openai_api_key, timeout=30.0, max_retries=1)
        
        # Generate image using DALL-E 3
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        # Get the image URL from response
        image_url = response.data[0].url
        
        print(f"[OK] DALL-E generated image: {image_url[:80]}...")
        return image_url
        
    except KeyboardInterrupt:
        # Re-raise keyboard interrupt to allow graceful shutdown
        raise
    except Exception as e:
        print(f"[ERROR] OpenAI image generation failed: {e}")
        return None


def create_image_prompt(title, category):
    """
    Create a detailed prompt for DALL-E to generate relevant news images.
    """
    # Extract key concepts from title
    keywords = extract_keywords(title, category)
    main_subject = ' '.join(keywords[:3]) if keywords else title
    
    # Category-specific style guidance
    category_styles = {
        'Technology': 'modern, futuristic, tech-focused, digital',
        'Business': 'professional, corporate, business environment',
        'Sports': 'dynamic, athletic, action-oriented, sports arena',
        'Entertainment': 'cinematic, artistic, entertainment industry',
        'Health': 'medical, healthcare, wellness-focused, clean',
        'Science': 'scientific, laboratory, research-oriented, educational',
        'Environment': 'natural, environmental, eco-friendly, nature',
        'Politics': 'governmental, political, official, serious',
        'General': 'journalistic, news-worthy, informative'
    }
    
    style = category_styles.get(category, 'journalistic, professional')
    
    # Create comprehensive prompt
    prompt = (
        f"Create a professional news article image about: {main_subject}. "
        f"Style: {style}. "
        f"The image should be photorealistic, high-quality, suitable for news media, "
        f"without any text or words, visually representing the concept of '{title[:100]}'. "
        f"Make it professional, clear, and engaging for news readers."
    )
    
    return prompt


def generate_image_with_unsplash(title, category):
    """
    Generate contextually relevant images based on headline keywords.
    Uses Unsplash Source API with article-specific keywords for relevant images.
    """
    
    # Try Pexels first - provides relevant, curated photos
    try:
        pexels_key = os.getenv('PEXELS_API_KEY')
        if pexels_key:
            # Extract keywords for search
            keywords = extract_keywords(title, category)
            search_query = ' '.join(keywords[:3]) if keywords else category
            
            headers = {'Authorization': pexels_key}
            response = requests.get(
                f'https://api.pexels.com/v1/search',
                headers=headers,
                params={'query': search_query, 'per_page': 1, 'orientation': 'landscape'},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('photos') and len(data['photos']) > 0:
                    photo_url = data['photos'][0]['src']['large']
                    print(f"[PEXELS] Found relevant image for: {search_query}")
                    return photo_url
    except Exception as e:
        print(f"[PEXELS] Failed: {e}")
    
    # Extract meaningful keywords from headline
    keywords = extract_keywords(title, category)
    
    # Use Unsplash API for better reliability
    try:
        search_term = ' '.join(keywords[:2]) if keywords and len(keywords) >= 2 else (keywords[0] if keywords else category)
        unsplash_response = requests.get(
            f'https://api.unsplash.com/search/photos',
            params={
                'query': search_term,
                'per_page': 1,
                'orientation': 'landscape'
            },
            headers={'Authorization': f'Client-ID {os.getenv("UNSPLASH_ACCESS_KEY", "")}'} if os.getenv("UNSPLASH_ACCESS_KEY") else {},
            timeout=5
        )
        
        if unsplash_response.status_code == 200:
            data = unsplash_response.json()
            if data.get('results') and len(data['results']) > 0:
                image_url = data['results'][0]['urls']['regular']
                print(f"[UNSPLASH] API image for '{search_term}': {title[:50]}")
                return image_url
    except:
        pass
    
    # Fallback to direct Unsplash photos (more reliable than source.unsplash.com)
    # Define category image pools
    category_image_pools = {
        'Technology': [
            'https://images.unsplash.com/photo-1518770660439-4636190af475?w=1024',  # Tech
            'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=1024',     # Circuit
            'https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?w=1024',  # Laptop
            'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1024',  # Data
            'https://images.unsplash.com/photo-1496171367470-9ed9a91ea931?w=1024',  # Code
        ],
        'Business': [
            'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1024',  # Office
            'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=1024',  # Business
            'https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=1024',  # Meeting
            'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1024',  # Charts
            'https://images.unsplash.com/photo-1553877522-43269d4ea984?w=1024',  # Handshake
        ],
        'Sports': [
            'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=1024',  # Sports
            'https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=1024',  # Stadium
            'https://images.unsplash.com/photo-1517649763962-0c623066013b?w=1024',  # Basketball
            'https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=1024',  # Soccer
            'https://images.unsplash.com/photo-1587329310686-91414b8e3cb7?w=1024',  # Athletics
        ],
        'Entertainment': [
            'https://images.unsplash.com/photo-1514306191717-452ec28c7814?w=1024',  # Cinema
            'https://images.unsplash.com/photo-1478737270239-2f02b77fc618?w=1024',  # Stage
            'https://images.unsplash.com/photo-1485846234645-a62644f84728?w=1024',  # Movie
            'https://images.unsplash.com/photo-1499364615650-ec38552f4f34?w=1024',  # Music
            'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=1024',  # Concert
        ],
        'Health': [
            'https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=1024',  # Medical
            'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1024',  # Doctor
            'https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?w=1024',  # Healthcare
            'https://images.unsplash.com/photo-1579154204601-01588f351e67?w=1024',  # Hospital
            'https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=1024',  # Wellness
        ],
        'Science': [
            'https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=1024',  # Lab
            'https://images.unsplash.com/photo-1507413245164-6160d8298b31?w=1024',  # Research
            'https://images.unsplash.com/photo-1628595351029-c2bf17511435?w=1024',  # Science
            'https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=1024',  # DNA
            'https://images.unsplash.com/photo-1567427017947-545c5f8d16ad?w=1024',  # Microscope
        ],
        'Politics': [
            'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=1024',  # Government
            'https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=1024',  # Capitol
            'https://images.unsplash.com/photo-1568092806323-8ec13f93eb1c?w=1024',  # Vote
            'https://images.unsplash.com/photo-1593115057322-e94b77572f20?w=1024',  # Democracy
            'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=1024',  # Politics
        ],
        'General': [
            'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1024',  # News
            'https://images.unsplash.com/photo-1495020689067-958852a7765e?w=1024',  # Newspaper
            'https://images.unsplash.com/photo-1563986768609-322da13575f3?w=1024',  # Journal
            'https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=1024',  # Breaking
            'https://images.unsplash.com/photo-1586339277861-b0b09f0d6a0f?w=1024',  # Media
        ],
    }
    
    # Get pool of images for category
    image_pool = category_image_pools.get(category, category_image_pools['General'])
    
    # Use title hash to deterministically select an image from the pool
    title_hash = int(hashlib.md5(title.encode()).hexdigest(), 16)
    selected_image = image_pool[title_hash % len(image_pool)]
    
    print(f"[UNSPLASH] Using varied category image for: {category}")
    return selected_image

def get_category_search_term(category):
    """Get relevant search terms for each category"""
    category_terms = {
        'Technology': 'technology,computer,innovation',
        'Business': 'business,office,corporate',
        'Sports': 'sports,athlete,competition',
        'Entertainment': 'entertainment,cinema,music',
        'Health': 'health,medical,wellness',
        'Science': 'science,laboratory,research',
        'Environment': 'nature,environment,ecology',
        'Politics': 'politics,government,capitol',
        'General': 'news,journalism,media'
    }
    return category_terms.get(category, 'news,newspaper')


def extract_keywords(title, category):
    """Extract meaningful keywords from title for image search"""
    # Common words to ignore
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
        'after', 'before', 'how', 'what', 'when', 'where', 'who', 'which', 'why',
        'says', 'said', 'new', 'just', 'now', 'over', 'about', 'into', 'through'
    }
    
    # Important keywords that should be prioritized
    priority_words = {
        'trump', 'biden', 'ohtani', 'sinatra', 'netflix', 'google', 'apple',
        'microsoft', 'tesla', 'spacex', 'nasa', 'olympics', 'championship',
        'election', 'war', 'peace', 'climate', 'covid', 'vaccine', 'economy'
    }
    
    # Split title into words and filter
    words = title.lower().split()
    keywords = []
    priority_keywords = []
    
    for word in words:
        # Remove punctuation but keep words
        word = ''.join(c for c in word if c.isalnum())
        
        # Check if it's a priority word
        if word in priority_words:
            priority_keywords.append(word)
        # Keep words that are meaningful and not stop words  
        elif len(word) > 3 and word not in stop_words:
            keywords.append(word)
    
    # Combine priority first, then regular keywords
    final_keywords = priority_keywords + keywords
    final_keywords = final_keywords[:5]  # Limit to 5 keywords
    
    # Add category as fallback
    if not final_keywords:
        final_keywords = [category]
    
    return final_keywords


def get_category_image(category):
    """Get a default image URL for a category using Picsum Photos"""
    seed = abs(hash(category.lower())) % 10000
    
    category_images = {
        'technology': f'https://picsum.photos/seed/tech{seed}/1024/1024',
        'business': f'https://picsum.photos/seed/biz{seed}/1024/1024',
        'sports': f'https://picsum.photos/seed/sports{seed}/1024/1024',
        'entertainment': f'https://picsum.photos/seed/entertain{seed}/1024/1024',
        'health': f'https://picsum.photos/seed/health{seed}/1024/1024',
        'science': f'https://picsum.photos/seed/science{seed}/1024/1024',
        'environment': f'https://picsum.photos/seed/nature{seed}/1024/1024',
        'politics': f'https://picsum.photos/seed/politics{seed}/1024/1024',
    }
    
    return category_images.get(category.lower(), 
                                f'https://picsum.photos/seed/news{seed}/1024/1024')
