from django.apps import AppConfig
import os
import sys


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        """
        Start background news fetcher when Django server starts
        Runs silently in a separate thread
        """
        # Temporarily disabled to allow server to start
        # Uncomment to enable background auto-fetching
        pass
        # Only run in the main process (not in reloader process)
        # if os.environ.get('RUN_MAIN') == 'true':
        #     import threading
        #     from datetime import datetime
        #     import logging
        #     
        #     # Configure logging to file only (silent terminal)
        #     log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'auto_fetcher.log')
        #     logging.basicConfig(
        #         filename=log_file,
        #         level=logging.INFO,
        #         format='%(asctime)s - %(levelname)s - %(message)s'
        #     )
        #     
        #     def start_auto_fetcher():
        #         """Start the auto-fetcher in background"""
        #         try:
        #             from .auto_fetcher_service import run_auto_fetcher
        #             logging.info("🚀 Starting background news auto-fetcher...")
        #             run_auto_fetcher()
        #         except Exception as e:
        #             logging.error(f"❌ Auto-fetcher error: {e}")
        #     
        #     # Start in daemon thread (won't block Django shutdown)
        #     fetcher_thread = threading.Thread(target=start_auto_fetcher, daemon=True)
        #     fetcher_thread.start()
