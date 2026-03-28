from django.core.management.base import BaseCommand
from api.services import news_fetcher
from api.ai_modules.sentiment_analysis import analyze_article_sentiment
from api.ai_modules.spam_detection import detect_article_spam
from api.models import NewsArticle
from api.utils.image_generator import generate_image_for_article
from dateutil import parser as date_parser
from django.utils import timezone
import json


class Command(BaseCommand):
    help = 'Fetch news articles and populate the database'

    def handle(self, *args, **kwargs):
        self.stdout.write('Fetching news articles...')
        
        try:
            # Fetch articles from NewsAPI
            articles_data = news_fetcher.fetch_news()
            
            created_count = 0
            for article_data in articles_data:
                try:
                    # Check if article already exists
                    existing = NewsArticle.objects.filter(url=article_data['url']).first()
                    if existing:
                        continue
                    
                    # Analyze sentiment (expects a dictionary)
                    try:
                        sentiment_score = analyze_article_sentiment(article_data)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'⚠ Sentiment analysis error: {e}'))
                        sentiment_score = 0.0
                    
                    # Detect spam (expects a dictionary)
                    try:
                        is_spam, spam_score, spam_reasons = detect_article_spam(article_data)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'⚠ Spam detection error: {e}'))
                        is_spam = False
                    
                    # Parse publish_time from ISO string to datetime object
                    publish_time = article_data.get('publish_time')
                    if isinstance(publish_time, str):
                        try:
                            publish_time = date_parser.parse(publish_time)
                        except:
                            publish_time = timezone.now()
                    elif not publish_time:
                        publish_time = timezone.now()
                    
                    # Generate image if not present
                    image_url = article_data.get('image_url', '')
                    if not image_url or image_url.strip() == '':
                        try:
                            image_url = generate_image_for_article(
                                article_data['title'],
                                article_data.get('category', 'General')
                            )
                            self.stdout.write(self.style.SUCCESS(f'🎨 Generated image for: {article_data["title"][:40]}...'))
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f'⚠ Image generation error: {e}'))
                            image_url = ''
                    
                    # Create article
                    NewsArticle.objects.create(
                        title=article_data['title'],
                        summary=article_data.get('summary', ''),
                        content=article_data.get('content', ''),
                        author=article_data.get('author', ''),
                        source=article_data.get('source', {}).get('name', 'Unknown') if isinstance(article_data.get('source'), dict) else str(article_data.get('source', 'Unknown')),
                        source_id=article_data.get('source_id', 'Unknown'),
                        url=article_data['url'],
                        image_url=image_url,
                        category=article_data.get('category', 'General'),
                        publish_time=publish_time,
                        sentiment_score=sentiment_score,
                        is_spam=is_spam
                    )
                    created_count += 1
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ Error saving article: {e}'))
                    continue
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} news articles')
            )
            
            total = NewsArticle.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f'Total articles in database: {total}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error fetching news: {str(e)}')
            )
