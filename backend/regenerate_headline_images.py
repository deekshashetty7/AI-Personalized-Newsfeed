"""
Regenerate images based on article headlines
Uses keyword extraction to find contextually relevant images
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_backend.settings')
django.setup()

from api.models import NewsArticle
from api.utils.image_generator import generate_image_for_article

print("\n" + "="*80)
print("🎨 REGENERATING IMAGES BASED ON HEADLINES")
print("="*80 + "\n")

# Process recent articles first (for testing)
articles = list(NewsArticle.objects.all().order_by('-publish_time')[:50])
total = len(articles)

print(f"Processing {total} most recent articles...\n")
print("Generating headline-based images:\n")

updated = 0
for i, article in enumerate(articles, 1):
    try:
        # Generate new image based on headline and category
        new_image = generate_image_for_article(article.title, article.category)
        
        if new_image:
            article.image_url = new_image
            article.save()
            updated += 1
            
            print(f"{i}. {article.title[:60]}")
            print(f"   Category: {article.category}")
            print(f"   Image: {new_image[:80]}...")
            print()
    except Exception as e:
        print(f"❌ Error processing article: {e}")

print("-" * 80)
print(f"\n✅ Successfully updated {updated}/{total} articles with headline-based images!")
print("\n💡 Images are now contextually relevant to each article's headline")
print("   Each article gets a unique image based on its content keywords\n")

print("="*80 + "\n")

# Show some examples
print("📋 SAMPLE RESULTS:\n")
sample_articles = NewsArticle.objects.all().order_by('-publish_time')[:5]
for article in sample_articles:
    print(f"Title: {article.title[:70]}")
    print(f"Image: {article.image_url}")
    print()
