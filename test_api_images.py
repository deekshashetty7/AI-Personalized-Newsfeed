import requests
import json
import urllib.parse

# First, get an article with image URL
try:
    r = requests.get('http://localhost:8000/api/news/', timeout=10)
    if r.status_code == 200:
        data = r.json()
        articles = data.get('results', []) if isinstance(data, dict) else data
        
        if articles:
            first_article = articles[0]
            image_url = first_article.get('image_url') or first_article.get('image')
            print(f"✓ Got {len(articles)} articles")
            print(f"✓ First article title: {first_article.get('title', 'N/A')[:60]}")
            print(f"✓ First article has image_url: {image_url[:80] if image_url else 'MISSING'}")
            
            if image_url:
                # Test the proxy
                encoded = urllib.parse.quote(image_url, safe='')
                proxy_url = f'http://localhost:8000/api/news/proxy-image/?url={encoded}'
                print(f"\nTesting proxy endpoint...")
                print(f"Original URL: {image_url[:80]}")
                
                r2 = requests.get(proxy_url, timeout=10)
                print(f"Proxy status: {r2.status_code}")
                print(f"Proxy content-type: {r2.headers.get('content-type')}")
                print(f"Proxy content length: {len(r2.content)} bytes")
                print(f"Proxy CORS header: {r2.headers.get('access-control-allow-origin', 'MISSING')}")
        else:
            print("✗ No articles returned")
    else:
        print(f"✗ API error: {r.status_code}")
except Exception as e:
    print(f"✗ Error: {str(e)[:200]}")
