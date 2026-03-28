"""
Management command to generate images for articles without images
"""
from django.core.management.base import BaseCommand
from django.db import models
from api.models import NewsArticle
from api.utils.image_generator import generate_image_for_article


class Command(BaseCommand):
    help = 'Generate images for articles that are missing images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Regenerate images for all articles (including those with images)',
        )

    def handle(self, *args, **options):
        regenerate_all = options.get('all', False)

        if regenerate_all:
            articles = NewsArticle.objects.all()
            self.stdout.write(f'Generating images for ALL {articles.count()} articles...')
        else:
            # Find articles without images
            articles = NewsArticle.objects.filter(
                models.Q(image_url='') | models.Q(image_url__isnull=True)
            )
            self.stdout.write(f'Found {articles.count()} articles without images')

        if articles.count() == 0:
            self.stdout.write(self.style.SUCCESS('✅ All articles already have images!'))
            return

        generated_count = 0
        failed_count = 0

        for article in articles:
            try:
                # Generate image based on title and category
                image_url = generate_image_for_article(article.title, article.category)
                
                # Update article
                article.image_url = image_url
                article.save(update_fields=['image_url'])
                
                generated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Generated image for: {article.title[:50]}...')
                )
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed for "{article.title[:50]}...": {e}')
                )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Complete! Generated {generated_count} images, {failed_count} failed'
            )
        )
