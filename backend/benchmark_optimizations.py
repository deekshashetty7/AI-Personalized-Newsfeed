#!/usr/bin/env python
"""
OPTIMIZATION VERIFICATION SCRIPT
Compares performance before and after optimizations
"""
import os
import sys
import django
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_backend.settings')
django.setup()

from api.services import NewsFetcher, fetch_all_sources_parallel


def test_sequential_fetch():
    """Test old sequential fetching"""
    print("\n" + "="*80)
    print("🐌 SEQUENTIAL FETCH (OLD METHOD)")
    print("="*80)
    
    fetcher = NewsFetcher()
    start = time.time()
    
    try:
        print("\n1️⃣  Fetching from NewsAPI...")
        newsapi = fetcher.fetch_top_headlines(category=None, page_size=50, days_back=7)
        t1 = time.time()
        print(f"   ✅ {len(newsapi)} articles ({t1-start:.1f}s)")
        
        print("2️⃣  Fetching from Reddit...")
        reddit = fetcher.fetch_from_reddit(limit=25)
        t2 = time.time()
        print(f"   ✅ {len(reddit)} articles ({t2-t1:.1f}s)")
        
        print("3️⃣  Fetching from RSS...")
        rss = fetcher.fetch_from_rss()
        t3 = time.time()
        print(f"   ✅ {len(rss)} articles ({t3-t2:.1f}s)")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        t3 = time.time()
    
    total_time = t3 - start
    print(f"\n⏱️  Total Sequential Time: {total_time:.1f} seconds")
    return total_time


def test_parallel_fetch():
    """Test new parallel fetching"""
    print("\n" + "="*80)
    print("⚡ PARALLEL FETCH (OPTIMIZED METHOD)")
    print("="*80)
    
    start = time.time()
    
    try:
        print("\n🔄 Fetching from all sources in parallel...")
        articles_with_source = fetch_all_sources_parallel()
        total_time = time.time() - start
        
        print(f"\n✅ Total articles: {len(articles_with_source)}")
        print(f"⏱️  Total Parallel Time: {total_time:.1f} seconds")
        
        return total_time
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return 0


def main():
    print("\n" + "="*80)
    print("📊 NEWS FETCHER OPTIMIZATION ANALYSIS")
    print(f"🕐 {datetime.now().strftime('%I:%M:%S %p, %B %d, %Y')}")
    print("="*80)
    
    # Test sequential
    seq_time = test_sequential_fetch()
    
    # Test parallel
    par_time = test_parallel_fetch()
    
    # Analysis
    if par_time > 0:
        speedup = seq_time / par_time
        improvement = ((seq_time - par_time) / seq_time) * 100
        
        print("\n" + "="*80)
        print("📈 PERFORMANCE IMPROVEMENT")
        print("="*80)
        print(f"Sequential Time:  {seq_time:.1f}s")
        print(f"Parallel Time:    {par_time:.1f}s")
        print(f"⚡ Speedup:       {speedup:.1f}x faster")
        print(f"📊 Improvement:   {improvement:.1f}%")
        print("="*80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Test stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
