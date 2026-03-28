"""
News fetching service - integrates with NewsAPI, RSS feeds and provides fallback data
Optimized for parallel fetching with ThreadPoolExecutor
"""

import requests
import feedparser
from datetime import datetime, timedelta
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class NewsFetcher:
    def __init__(self):
        self.api_key = settings.NEWS_API_KEY
        self.gnews_api_key = getattr(settings, 'GNEWS_API_KEY', None)
        self.rss_api_key = getattr(settings, 'RSS_API_KEY', None)
        self.twitter_bearer_token = getattr(settings, 'TWITTER_BEARER_TOKEN', None)
        self.base_url = "https://newsapi.org/v2"
        self.gnews_base_url = "https://gnews.io/api/v4"
        self.rss_base_url = "https://api.rss2json.com/v1/api.json"
        self.twitter_api_url = "https://api.twitter.com/2"
        
        # Hardcoded fallback news data
        self.fallback_news = [
            {
                "title": "Artificial Intelligence Breakthrough: New Model Surpasses Human Performance",
                "description": "Researchers announce a groundbreaking AI system that demonstrates unprecedented capabilities in understanding and generating human-like responses.",
                "content": "In a landmark achievement, scientists have developed an AI model that shows remarkable improvements in natural language understanding and generation. The system demonstrates enhanced reasoning capabilities and can engage in more nuanced conversations than previous models.",
                "url": "https://example.com/ai-breakthrough",
                "image_url": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800",
                "publishedAt": datetime.now().isoformat(),
                "source": {"name": "Tech News Daily"},
                "author": "Dr. Sarah Johnson",
                "category": "Technology"
            },
            {
                "title": "Global Climate Summit Reaches Historic Agreement",
                "description": "World leaders unite to commit to ambitious carbon reduction targets in unprecedented climate deal.",
                "content": "Representatives from over 190 countries have signed a comprehensive climate agreement that sets binding targets for reducing greenhouse gas emissions. The accord includes provisions for transitioning to renewable energy and protecting biodiversity.",
                "url": "https://example.com/climate-summit",
                "image_url": "https://images.unsplash.com/photo-1569163139394-de4798aa62b6?w=800",
                "publishedAt": (datetime.now() - timedelta(hours=2)).isoformat(),
                "source": {"name": "Global News Network"},
                "author": "Michael Chen",
                "category": "Environment"
            },
            {
                "title": "Stock Markets Hit Record Highs Amid Economic Recovery",
                "description": "Major indices reach all-time peaks as investors show renewed confidence in economic growth.",
                "content": "Financial markets experienced significant gains today with major indices closing at record levels. Analysts attribute the surge to positive economic indicators and strong corporate earnings reports. Tech stocks led the rally with notable gains across the sector.",
                "url": "https://example.com/market-highs",
                "image_url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800",
                "publishedAt": (datetime.now() - timedelta(hours=4)).isoformat(),
                "source": {"name": "Financial Times"},
                "author": "Emma Williams",
                "category": "Business"
            },
            {
                "title": "Revolutionary Medical Treatment Shows Promise in Clinical Trials",
                "description": "New therapy demonstrates remarkable effectiveness in treating previously incurable diseases.",
                "content": "A groundbreaking medical treatment has shown exceptional results in Phase 3 clinical trials. The innovative approach combines gene therapy with personalized medicine to target specific disease markers, offering hope to millions of patients worldwide.",
                "url": "https://example.com/medical-breakthrough",
                "image_url": "https://images.unsplash.com/photo-1579154204601-01588f351e67?w=800",
                "publishedAt": (datetime.now() - timedelta(hours=6)).isoformat(),
                "source": {"name": "Medical Journal Today"},
                "author": "Dr. Robert Martinez",
                "category": "Health"
            },
            {
                "title": "Space Exploration Milestone: New Mission to Mars Announced",
                "description": "International space agency reveals ambitious plans for manned mission to the Red Planet.",
                "content": "In an exciting development for space exploration, plans for a crewed mission to Mars have been unveiled. The multi-year project will involve collaboration between space agencies worldwide and aims to establish the first human presence on Mars by the end of the decade.",
                "url": "https://example.com/mars-mission",
                "image_url": "https://images.unsplash.com/photo-1614728894747-a83421e2b9c9?w=800",
                "publishedAt": (datetime.now() - timedelta(hours=8)).isoformat(),
                "source": {"name": "Space News Daily"},
                "author": "Lisa Anderson",
                "category": "Science"
            },
            {
                "title": "Major Sports Championship Delivers Thrilling Finale",
                "description": "Underdog team secures victory in dramatic final match that captivated millions.",
                "content": "In an unforgettable championship game, the underdog team staged a remarkable comeback to claim victory. The match went into overtime with both teams displaying exceptional skill and determination. Fans worldwide celebrated the historic win that will be remembered for years to come.",
                "url": "https://example.com/sports-championship",
                "image_url": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800",
                "publishedAt": (datetime.now() - timedelta(hours=10)).isoformat(),
                "source": {"name": "Sports Illustrated"},
                "author": "Tom Bradley",
                "category": "Sports"
            },
            {
                "title": "Entertainment Industry Unveils Groundbreaking Virtual Reality Experience",
                "description": "New VR platform promises to revolutionize how audiences consume entertainment content.",
                "content": "A major entertainment company has launched an innovative virtual reality platform that offers immersive experiences unlike anything seen before. The technology allows users to interact with content in unprecedented ways, potentially transforming the entertainment landscape.",
                "url": "https://example.com/vr-entertainment",
                "image_url": "https://images.unsplash.com/photo-1622979135225-d2ba269cf1ac?w=800",
                "publishedAt": (datetime.now() - timedelta(hours=12)).isoformat(),
                "source": {"name": "Entertainment Weekly"},
                "author": "Jennifer Lopez",
                "category": "Entertainment"
            },
            {
                "title": "Education Revolution: AI-Powered Learning Platforms Gain Momentum",
                "description": "New educational technology adapts to individual learning styles, showing remarkable results.",
                "content": "Artificial intelligence is transforming education with personalized learning platforms that adapt to each student's unique needs. Early adopters report significant improvements in student engagement and academic performance. Educators praise the technology for its ability to identify and address learning gaps.",
                "url": "https://example.com/ai-education",
                "image_url": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800",
                "publishedAt": (datetime.now() - timedelta(hours=14)).isoformat(),
                "source": {"name": "Education Today"},
                "author": "Dr. Amanda Taylor",
                "category": "Education"
            },
            {
                "title": "Cybersecurity Experts Warn of New Threat Landscape",
                "description": "Security researchers identify emerging vulnerabilities requiring immediate attention.",
                "content": "Leading cybersecurity experts have identified new threats that could impact organizations worldwide. The sophisticated attack vectors exploit previously unknown vulnerabilities. Security teams are urged to implement updated protection measures and stay vigilant against evolving threats.",
                "url": "https://example.com/cybersecurity-alert",
                "image_url": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800",
                "publishedAt": (datetime.now() - timedelta(hours=16)).isoformat(),
                "source": {"name": "Security Weekly"},
                "author": "James Wilson",
                "category": "Technology"
            },
            {
                "title": "Sustainable Energy Initiative Exceeds Targets Ahead of Schedule",
                "description": "Renewable energy project achieves milestones faster than anticipated, offering blueprint for future developments.",
                "content": "A major renewable energy initiative has surpassed its initial targets two years ahead of schedule. The project successfully demonstrates the viability of large-scale sustainable energy production. Industry experts suggest this success could accelerate the global transition to clean energy.",
                "url": "https://example.com/sustainable-energy",
                "image_url": "https://images.unsplash.com/photo-1466611653911-95081537e5b7?w=800",
                "publishedAt": (datetime.now() - timedelta(hours=18)).isoformat(),
                "source": {"name": "Green Energy Magazine"},
                "author": "Rachel Green",
                "category": "Environment"
            }
        ]
    
    def fetch_from_gnews(self, category=None, page_size=100):
        """Fetch latest news from GNews API (provides more recent news than NewsAPI free tier)"""
        if not self.gnews_api_key:
            return []
        
        try:
            endpoint = f"{self.gnews_base_url}/top-headlines"
            params = {
                'apikey': self.gnews_api_key,
                'lang': 'en',
                'max': min(page_size, 100)  # GNews max is 100
            }
            
            if category and category.lower() != 'all':
                # GNews categories: general, world, nation, business, technology, entertainment, sports, science, health
                params['topic'] = category.lower()
            
            response = requests.get(endpoint, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                # Convert GNews format to NewsAPI-compatible format
                converted_articles = []
                for article in articles:
                    converted_articles.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'content': article.get('content', ''),
                        'url': article.get('url', ''),
                        'urlToImage': article.get('image', ''),
                        'publishedAt': article.get('publishedAt', ''),
                        'source': {'name': article.get('source', {}).get('name', 'Unknown')},
                        'author': '',  # GNews doesn't provide author
                        'category': category or 'General'
                    })
                
                print(f"✅ Fetched {len(converted_articles)} articles from GNews API")
                return converted_articles
            else:
                print(f"GNews API HTTP error: {response.status_code}")
                return []
        
        except Exception as e:
            print(f"GNews API error: {e}")
            return []
    
    def fetch_top_headlines(self, category=None, country='us', page=1, page_size=100, days_back=7):
        """
        Fetch top headlines from latest + past 7 days
        Filters articles to only include recent news (today + last 7 days)
        """
        # Calculate date range: today and past 7 days
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)
        
        print(f"[FETCH] Fetching news from {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}")
        
        # Try GNews first if available (provides more recent news)
        if self.gnews_api_key:
            articles = self.fetch_from_gnews(category=category, page_size=page_size)
            if articles:
                # Filter by date
                articles = self._filter_by_date_range(articles, from_date, to_date)
                return articles
        
        # Fallback to NewsAPI
        try:
            all_articles = []
            max_pages = 2  # OPTIMIZED: Reduced from 5 to 2 pages for faster fetching
            actual_page_size = min(page_size, 100)  # NewsAPI max is 100 per request
            
            for current_page in range(1, max_pages + 1):
                endpoint = f"{self.base_url}/top-headlines"
                params = {
                    'apiKey': self.api_key,
                    'country': country,
                    'page': current_page,
                    'pageSize': actual_page_size
                }
                
                if category:
                    params['category'] = category
                
                response = requests.get(endpoint, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'ok':
                        articles = data.get('articles', [])
                        all_articles.extend(articles)
                        
                        # If we got less than requested, we've reached the end
                        if len(articles) < actual_page_size:
                            break
                    else:
                        print(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                        break
                else:
                    print(f"NewsAPI HTTP error: {response.status_code}")
                    break
            
            if all_articles:
                # Filter by date range (today + 7 days)
                all_articles = self._filter_by_date_range(all_articles, from_date, to_date)
                print(f"✅ Fetched {len(all_articles)} recent articles from NewsAPI (last {days_back} days)")
                return all_articles
            
            # Fallback to hardcoded data if API fails
            return self._get_fallback_news(category)
        
        except Exception as e:
            print(f"NewsAPI error: {e}")
            return self._get_fallback_news(category)
    
    def fetch_everything(self, query, from_date=None, to_date=None, page=1, page_size=100):
        """Fetch all news matching query - unlimited articles through multiple requests"""
        try:
            all_articles = []
            max_pages = 10  # Fetch from multiple pages for extensive results
            actual_page_size = min(page_size, 100)  # NewsAPI max is 100 per request
            
            for current_page in range(1, max_pages + 1):
                endpoint = f"{self.base_url}/everything"
                params = {
                    'apiKey': self.api_key,
                    'q': query,
                    'page': current_page,
                    'pageSize': actual_page_size,
                    'sortBy': 'publishedAt'
                }
                
                if from_date:
                    params['from'] = from_date
                if to_date:
                    params['to'] = to_date
                
                response = requests.get(endpoint, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'ok':
                        articles = data.get('articles', [])
                        all_articles.extend(articles)
                        
                        # If we got less than requested, we've reached the end
                        if len(articles) < actual_page_size:
                            break
                    else:
                        print(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                        break
                else:
                    print(f"NewsAPI HTTP error: {response.status_code}")
                    break
            
            if all_articles:
                print(f"✅ Fetched {len(all_articles)} articles from NewsAPI everything endpoint")
                return all_articles
            
            return self._get_fallback_news()
        
        except Exception as e:
            print(f"NewsAPI error: {e}")
            return self._get_fallback_news()
    
    def fetch_from_rss(self, rss_url=None, count=100):
        """Fetch news from RSS feeds - parses RSS directly without external API"""
        try:
            # Multiple RSS feeds for better coverage
            if not rss_url:
                rss_feeds = [
                    'https://feeds.bbci.co.uk/news/world/rss.xml',  # BBC World
                    'https://rss.cnn.com/rss/cnn_topstories.rss',  # CNN Top Stories
                    'https://feeds.npr.org/1001/rss.xml',  # NPR News
                    'https://www.theguardian.com/world/rss',  # Guardian World
                    'https://feeds.reuters.com/reuters/topNews',  # Reuters
                ]
                
                all_articles = []
                for feed_url in rss_feeds:
                    try:
                        print(f"📡 Fetching RSS feed: {feed_url}")
                        feed = feedparser.parse(feed_url)
                        
                        for entry in feed.entries[:20]:  # Get 20 from each feed
                            # Parse publish date
                            pub_date = entry.get('published', entry.get('updated', ''))
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                pub_date = datetime(*entry.published_parsed[:6]).isoformat() + 'Z'
                            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                                pub_date = datetime(*entry.updated_parsed[:6]).isoformat() + 'Z'
                            else:
                                pub_date = datetime.now().isoformat() + 'Z'
                            
                            # Get image
                            image_url = ''
                            if hasattr(entry, 'media_content'):
                                image_url = entry.media_content[0].get('url', '') if entry.media_content else ''
                            elif hasattr(entry, 'media_thumbnail'):
                                image_url = entry.media_thumbnail[0].get('url', '') if entry.media_thumbnail else ''
                            
                            all_articles.append({
                                'title': entry.get('title', ''),
                                'description': entry.get('summary', ''),
                                'content': entry.get('content', [{}])[0].get('value', entry.get('summary', '')) if hasattr(entry, 'content') else entry.get('summary', ''),
                                'url': entry.get('link', ''),
                                'urlToImage': image_url,
                                'publishedAt': pub_date,
                                'source': {'name': feed.feed.get('title', 'RSS Feed')},
                                'author': entry.get('author', ''),
                                'category': 'General'
                            })
                    
                    except Exception as feed_error:
                        print(f"⚠️ Error parsing RSS feed {feed_url}: {feed_error}")
                        continue
                
                if all_articles:
                    print(f"✅ Fetched {len(all_articles)} articles from RSS feeds")
                    return all_articles[:count]
                
                return []
            
            return []
        
        except Exception as e:
            print(f"❌ RSS error: {e}")
            return []
    
    def fetch_from_twitter(self, query="breaking news", max_results=20):
        """Fetch news from Twitter API v2"""
        if not self.twitter_bearer_token:
            print("⚠️ Twitter Bearer Token not configured")
            return []
        
        try:
            endpoint = f"{self.twitter_api_url}/tweets/search/recent"
            headers = {
                'Authorization': f'Bearer {self.twitter_bearer_token}'
            }
            params = {
                'query': f'{query} -is:retweet lang:en',
                'max_results': max_results,
                'tweet.fields': 'created_at,author_id,public_metrics,entities',
                'expansions': 'author_id,attachments.media_keys',
                'media.fields': 'url,preview_image_url',
                'user.fields': 'name,username,verified'
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                # Create user lookup
                users = {user['id']: user for user in data.get('includes', {}).get('users', [])}
                media = {m['media_key']: m for m in data.get('includes', {}).get('media', [])}
                
                for tweet in data.get('data', []):
                    author_id = tweet.get('author_id')
                    user = users.get(author_id, {})
                    
                    # Get media if available
                    image_url = ''
                    if 'attachments' in tweet and 'media_keys' in tweet['attachments']:
                        media_key = tweet['attachments']['media_keys'][0]
                        media_item = media.get(media_key, {})
                        image_url = media_item.get('url', media_item.get('preview_image_url', ''))
                    
                    tweet_url = f"https://twitter.com/{user.get('username', 'i')}/status/{tweet['id']}"
                    
                    articles.append({
                        'title': tweet['text'][:100] + ('...' if len(tweet['text']) > 100 else ''),
                        'description': tweet['text'],
                        'content': tweet['text'],
                        'url': tweet_url,
                        'urlToImage': image_url,
                        'publishedAt': tweet.get('created_at', datetime.now().isoformat()),
                        'source': {'name': 'Twitter'},
                        'author': f"@{user.get('username', 'unknown')}",
                        'category': 'Social Media'
                    })
                
                if articles:
                    print(f"✅ Fetched {len(articles)} tweets from Twitter")
                return articles
            else:
                print(f"⚠️ Twitter API returned status {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Twitter API error: {e}")
            return []
    
    def fetch_from_reddit(self, subreddits=None, limit=25):
        """Fetch news from Reddit using public JSON feeds (no API key needed)"""
        if subreddits is None:
            # Default news subreddits
            subreddits = [
                'worldnews', 'news', 'technology', 'science',
                'business', 'sports', 'entertainment', 'health'
            ]
        
        articles = []
        
        for subreddit in subreddits:
            try:
                # Reddit's public JSON endpoint
                url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                headers = {'User-Agent': 'InfoCred News Aggregator 1.0'}
                
                response = requests.get(url, headers=headers, params={'limit': limit}, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    
                    for post in posts:
                        post_data = post.get('data', {})
                        
                        # Skip pinned/stickied posts and non-article posts
                        if post_data.get('stickied') or post_data.get('is_self'):
                            continue
                        
                        # Get thumbnail or preview image
                        image_url = ''
                        if post_data.get('thumbnail') and post_data['thumbnail'].startswith('http'):
                            image_url = post_data['thumbnail']
                        elif 'preview' in post_data and 'images' in post_data['preview']:
                            images = post_data['preview']['images']
                            if images and 'source' in images[0]:
                                image_url = images[0]['source'].get('url', '').replace('&amp;', '&')
                        
                        # Map subreddit to category
                        category_map = {
                            'worldnews': 'Politics',
                            'news': 'General',
                            'technology': 'Technology',
                            'science': 'Science',
                            'business': 'Business',
                            'sports': 'Sports',
                            'entertainment': 'Entertainment',
                            'health': 'Health'
                        }
                        
                        # Get article URL (prefer external link, fallback to Reddit post)
                        article_url = post_data.get('url', '')
                        if 'reddit.com' in article_url or not article_url:
                            article_url = f"https://www.reddit.com{post_data.get('permalink', '')}"
                        
                        articles.append({
                            'title': post_data.get('title', 'Untitled'),
                            'description': post_data.get('selftext', '')[:200] or post_data.get('title', ''),
                            'content': post_data.get('selftext', '') or post_data.get('title', ''),
                            'url': article_url,
                            'urlToImage': image_url,
                            'publishedAt': datetime.fromtimestamp(post_data.get('created_utc', 0)).isoformat(),
                            'source': {'name': f'Reddit - r/{subreddit}'},
                            'author': f"u/{post_data.get('author', 'unknown')}",
                            'category': category_map.get(subreddit, 'General')
                        })
                    
                    print(f"✅ Fetched {len(posts)} posts from r/{subreddit}")
                else:
                    print(f"⚠️ Reddit r/{subreddit} returned status {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Reddit r/{subreddit} error: {e}")
                continue
        
        if articles:
            print(f"📰 Total Reddit articles: {len(articles)}")
        return articles
    
    def fetch_news(self, category=None, use_rss=True, unlimited=False, use_twitter=True, use_reddit=True):
        """Fetch news from ALL available sources - NewsAPI, GNews, and RSS combined"""
        all_articles = []
        
        # 1. Fetch from NewsAPI
        try:
            newsapi_articles = self.fetch_top_headlines(category=category, page_size=100)
            if newsapi_articles:
                for article in newsapi_articles:
                    article['source_name'] = 'NewsAPI'
                    if category:
                        article['category'] = category.capitalize()
                all_articles.extend(newsapi_articles)
                print(f"📰 Added {len(newsapi_articles)} articles from NewsAPI")
        except Exception as e:
            print(f"⚠️ NewsAPI error: {e}")
        
        # 2. Fetch from GNews
        try:
            gnews_articles = self.fetch_from_gnews(category=category, page_size=100)
            if gnews_articles:
                for article in gnews_articles:
                    article['source_name'] = 'GNews'
                all_articles.extend(gnews_articles)
                print(f"📰 Added {len(gnews_articles)} articles from GNews")
        except Exception as e:
            print(f"⚠️ GNews error: {e}")
        
        # 3. Fetch from RSS feeds
        if use_rss:
            try:
                rss_articles = self.fetch_from_rss()
                if rss_articles:
                    for article in rss_articles:
                        article['source_name'] = 'RSS'
                    all_articles.extend(rss_articles)
                    print(f"📰 Added {len(rss_articles)} articles from RSS")
            except Exception as e:
                print(f"⚠️ RSS error: {e}")
        
        # 4. Fetch from Twitter (optional)
        if use_twitter:
            try:
                twitter_articles = self.fetch_from_twitter()
                if twitter_articles:
                    for article in twitter_articles:
                        article['source_name'] = 'Twitter'
                    all_articles.extend(twitter_articles)
                    print(f"🐦 Added {len(twitter_articles)} articles from Twitter")
            except Exception as e:
                print(f"⚠️ Twitter error: {e}")
        
        # 5. Fetch from Reddit (optional)
        if use_reddit:
            try:
                reddit_articles = self.fetch_from_reddit()
                if reddit_articles:
                    for article in reddit_articles:
                        article['source_name'] = 'Reddit'
                    all_articles.extend(reddit_articles)
                    print(f"📰 Added {len(reddit_articles)} articles from Reddit")
            except Exception as e:
                print(f"⚠️ Reddit error: {e}")
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        if unique_articles:
            import random
            random.shuffle(unique_articles)  # Mix articles from all sources
            print(f"✅ Total unique articles from all sources: {len(unique_articles)}")
            return unique_articles
        
        # If all sources fail, return fallback news
        print(f"⚠️ All sources failed, using fallback news")
        return self._get_fallback_news(category)
    
    def _filter_by_date_range(self, articles, from_date, to_date):
        """Filter articles to only include those within the date range"""
        from dateutil import parser as date_parser
        
        filtered = []
        for article in articles:
            try:
                pub_date_str = article.get('publishedAt', article.get('publish_time', ''))
                if pub_date_str:
                    pub_date = date_parser.parse(pub_date_str)
                    # Make timezone-naive for comparison if needed
                    if pub_date.tzinfo:
                        pub_date = pub_date.replace(tzinfo=None)
                    
                    # Check if within date range
                    if from_date <= pub_date <= to_date:
                        filtered.append(article)
                else:
                    # If no date, include it (assume recent)
                    filtered.append(article)
            except Exception as e:
                # If date parsing fails, include the article
                print(f"[WARN] Date parsing error for article: {e}")
                filtered.append(article)
        
        return filtered
    
    def _get_fallback_news(self, category=None):
        """Return hardcoded fallback news"""
        if category:
            return [article for article in self.fallback_news 
                   if article.get('category', '').lower() == category.lower()]
        return self.fallback_news
    
    def normalize_article(self, article):
        """Normalize article data from API or fallback"""
        from django.utils import timezone
        
        # Parse publish time and make it timezone-aware
        publish_time_str = article.get('publishedAt', article.get('publish_time', ''))
        if publish_time_str:
            try:
                from dateutil import parser
                parsed_time = parser.parse(publish_time_str)
                # Make timezone-aware if naive
                if parsed_time.tzinfo is None:
                    parsed_time = timezone.make_aware(parsed_time)
                publish_time = parsed_time.isoformat()
            except:
                publish_time = timezone.now().isoformat()
        else:
            publish_time = timezone.now().isoformat()
        
        return {
            'title': article.get('title', ''),
            'summary': article.get('description', ''),
            'content': article.get('content', article.get('description', '')),
            'url': article.get('url', ''),
            'image_url': article.get('urlToImage', article.get('image_url', '')),
            'publish_time': publish_time,
            'source': article.get('source', {}).get('name', article.get('source_name', 'Unknown')) if isinstance(article.get('source'), dict) else str(article.get('source', article.get('source_name', 'Unknown'))),
            'source_id': article.get('source', {}).get('id', article.get('source', {}).get('name', 'Unknown')) if isinstance(article.get('source'), dict) else str(article.get('source', 'Unknown')),
            'author': article.get('author', ''),
            'category': article.get('category', 'General')
        }


def fetch_all_sources_parallel():
    """
    OPTIMIZED: Fetch from all sources in parallel using ThreadPoolExecutor
    Returns list of (article, source_name) tuples from NewsAPI, Reddit, and RSS simultaneously
    This is significantly faster than sequential fetching
    """
    fetcher = NewsFetcher()
    all_articles = []
    lock = threading.Lock()
    
    def fetch_newsapi():
        try:
            articles = fetcher.fetch_top_headlines(category=None, page_size=50, days_back=7)
            with lock:
                all_articles.extend([(a, 'NewsAPI') for a in articles])
            print(f"✅ NewsAPI: {len(articles)} articles")
        except Exception as e:
            print(f"⚠️ NewsAPI fetch failed: {e}")
    
    def fetch_reddit():
        try:
            articles = fetcher.fetch_from_reddit(limit=25)  # Reduced from 30
            with lock:
                all_articles.extend([(a, 'Reddit') for a in articles])
            print(f"✅ Reddit: {len(articles)} articles")
        except Exception as e:
            print(f"⚠️ Reddit fetch failed: {e}")
    
    def fetch_rss():
        try:
            articles = fetcher.fetch_from_rss()
            with lock:
                all_articles.extend([(a, 'RSS') for a in articles])
            print(f"✅ RSS: {len(articles)} articles")
        except Exception as e:
            print(f"⚠️ RSS fetch failed: {e}")
    
    # Execute all fetches in parallel using thread pool
    print("\n📡 Fetching from NewsAPI, Reddit, and RSS in parallel...")
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(fetch_newsapi),
            executor.submit(fetch_reddit),
            executor.submit(fetch_rss)
        ]
        
        # Wait for all to complete with timeout
        for future in as_completed(futures, timeout=30):
            try:
                future.result()
            except Exception as e:
                print(f"⚠️ Parallel fetch worker error: {e}")
    
    print(f"✅ Parallel fetch complete: {len(all_articles)} total articles fetched")
    return all_articles


# Global instance
news_fetcher = NewsFetcher()
