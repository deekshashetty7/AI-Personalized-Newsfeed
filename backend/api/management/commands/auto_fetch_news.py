"""
Management command to run continuous news fetching in background
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
import schedule
import time
from datetime import datetime


class Command(BaseCommand):
    help = 'Run continuous news fetching in background'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Interval in minutes between fetches (default: 30)',
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Fetch once and exit (no continuous mode)',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        once = options['once']

        if once:
            # Just fetch once and exit
            self.stdout.write('Fetching news once...')
            call_command('fetch_news')
            self.stdout.write(self.style.SUCCESS('✅ Fetch complete!'))
            return

        # Continuous mode
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('🚀 Starting Continuous News Fetcher'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'⏰ Fetch interval: Every {interval} minutes')
        self.stdout.write(f'📰 Sources: RSS Feeds, NewsAPI, Twitter')
        self.stdout.write(f'🎯 Press Ctrl+C to stop')
        self.stdout.write('=' * 80)
        self.stdout.write('')

        def fetch_task():
            """Fetch news task"""
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.stdout.write('')
            self.stdout.write('=' * 80)
            self.stdout.write(f'🔄 Auto-fetching news at {timestamp}')
            self.stdout.write('=' * 80)
            
            try:
                call_command('fetch_news')
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('✅ Auto-fetch completed!'))
                self.stdout.write(f'⏰ Next fetch in {interval} minutes')
                self.stdout.write('=' * 80)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Auto-fetch failed: {e}'))

        # Fetch immediately on start
        fetch_task()

        # Schedule periodic fetches
        schedule.every(interval).minutes.do(fetch_task)

        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.stdout.write('')
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('🛑 News fetcher stopped by user'))
