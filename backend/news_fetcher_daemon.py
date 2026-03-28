"""
Background news fetcher that runs continuously
Fetches news every 30 minutes
"""
import time
import schedule
from django.core.management import call_command
from datetime import datetime


def fetch_news_task():
    """Task to fetch news from all sources"""
    print(f"\n{'='*80}")
    print(f"🔄 Auto-fetching news at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    try:
        # Fetch news from all sources
        call_command('fetch_news')
        print(f"\n✅ Auto-fetch completed successfully!\n")
    except Exception as e:
        print(f"\n❌ Auto-fetch failed: {e}\n")


def start_scheduler():
    """Start the background scheduler"""
    print(f"\n{'='*80}")
    print("🚀 Starting News Auto-Fetcher")
    print(f"{'='*80}")
    print(f"⏰ Will fetch news every 30 minutes")
    print(f"📰 Sources: RSS Feeds, NewsAPI, Twitter")
    print(f"🎯 Press Ctrl+C to stop")
    print(f"{'='*80}\n")
    
    # Fetch immediately on start
    fetch_news_task()
    
    # Schedule to run every 30 minutes
    schedule.every(30).minutes.do(fetch_news_task)
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == '__main__':
    import os
    import sys
    import django
    
    # Setup Django
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_backend.settings')
    django.setup()
    
    try:
        start_scheduler()
    except KeyboardInterrupt:
        print("\n\n🛑 News auto-fetcher stopped by user")
        sys.exit(0)
