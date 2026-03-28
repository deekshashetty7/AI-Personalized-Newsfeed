"""
Django management command to validate and fix all article images
Usage: python manage.py fix_images
"""
from django.core.management.base import BaseCommand
from api.models import NewsArticle
from django.db.models import Q
import hashlib


class Command(BaseCommand):
    help = 'Validate and fix missing or invalid article images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of articles to process',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        dry_run = options.get('dry_run', False)

        self.stdout.write(self.style.SUCCESS('\n🔍 Scanning for articles with missing/invalid images...\n'))

        # Find articles with missing or invalid images
        articles = NewsArticle.objects.filter(
            Q(image_url__isnull=True) | 
            Q(image_url='') | 
            Q(image_url__contains='source.unsplash.com') |
            Q(image_url__contains='placeholder')
        )

        if limit:
            articles = articles[:limit]

        total = articles.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ All articles have valid images!\n'))
            return

        self.stdout.write(f'📊 Found {total} articles needing image fixes\n')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  DRY RUN MODE - No changes will be made\n'))

        fixed = 0
        errors = 0

        for idx, article in enumerate(articles, 1):
            try:
                old_image = article.image_url or 'None'
                
                # Generate new image URL
                seed_text = f"{article.category}-{article.title[:30]}"
                seed = hashlib.md5(seed_text.encode()).hexdigest()[:8]
                new_image = f"https://picsum.photos/seed/{seed}/1024/1024"
                
                if dry_run:
                    self.stdout.write(f'[{idx}/{total}] Would fix: {article.title[:60]}')
                    self.stdout.write(f'  Old: {old_image}')
                    self.stdout.write(f'  New: {new_image}\n')
                else:
                    article.image_url = new_image
                    article.save()
                    fixed += 1
                    
                    if idx % 50 == 0:
                        self.stdout.write(f'[{idx}/{total}] Processing...')
                
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'❌ Error: {article.title[:40]}: {e}'))

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Dry run complete! Would fix {total} articles'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Fixed {fixed} articles!'))
            if errors > 0:
                self.stdout.write(self.style.WARNING(f'⚠️  {errors} errors occurred'))
            
            # Show updated stats
            remaining = NewsArticle.objects.filter(
                Q(image_url__isnull=True) | 
                Q(image_url='') | 
                Q(image_url__contains='source.unsplash.com')
            ).count()
            
            self.stdout.write(f'\n📊 Remaining articles with issues: {remaining}')
