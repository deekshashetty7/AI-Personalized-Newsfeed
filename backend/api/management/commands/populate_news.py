"""
Management command to populate database with news articles
"""

from django.core.management.base import BaseCommand
from api.models import NewsArticle, NewsSource
from api.services import news_fetcher
from api.ai_modules.sentiment_analysis import analyze_article_sentiment
from api.ai_modules.spam_detection import detect_article_spam
from dateutil import parser as date_parser
from django.utils import timezone


class Command(BaseCommand):
    help = 'Populate database with news articles from APIs'

    def add_arguments(self, parser):
        parser.add_argument('--category', type=str, help='News category to fetch')
        parser.add_argument('--count', type=int, default=50, help='Number of articles to fetch')

    def handle(self, *args, **options):
        category = options.get('category')
        count = options.get('count', 50)

        self.stdout.write(f'Fetching {count} articles for category: {category or "all"}')

        try:
            # Fetch articles from API
            api_articles = news_fetcher.fetch_top_headlines(
                category=category,
                page_size=count
            )

            saved_count = 0
            skipped_count = 0

            for article_data in api_articles:
                try:
                    normalized = news_fetcher.normalize_article(article_data)

                    # Check if article already exists
                    existing = NewsArticle.objects.filter(title=normalized['title']).first()
                    if existing:
                        skipped_count += 1
                        continue

                    # Analyze sentiment
                    try:
                        sentiment_score = analyze_article_sentiment(normalized)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'⚠ Sentiment analysis error: {e}'))
                        sentiment_score = 0.0

                    # Detect spam
                    try:
                        is_spam, spam_score, spam_reasons = detect_article_spam(normalized)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'⚠ Spam detection error: {e}'))
                        is_spam = False
                        spam_score = 0.0
                        spam_reasons = []

                    # Parse publish_time from ISO string to datetime object
                    publish_time = normalized['publish_time']
                    if isinstance(publish_time, str):
                        try:
                            publish_time = date_parser.parse(publish_time)
                        except:
                            publish_time = timezone.now()

                    # Create article
                    article = NewsArticle.objects.create(
                        title=normalized['title'],
                        summary=normalized['summary'],
                        content=normalized['content'],
                        category=normalized['category'],
                        source_id=normalized['source_id'] or 'Unknown',
                        url=normalized['url'] or '',
                        image_url=normalized['image_url'] or '',
                        author=normalized['author'] or '',
                        publish_time=publish_time,
                        sentiment_score=sentiment_score,
                        is_spam=is_spam
                    )
                    saved_count += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Saved: {article.title[:50]}...')
                    )
                
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error processing article: {e}')
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Complete! Saved {saved_count} articles, skipped {skipped_count} duplicates'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error fetching articles: {e}')
            )