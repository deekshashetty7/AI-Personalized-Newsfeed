import requests
import urllib.parse

# Get an article image URL from the API
r = requests.get('http://localhost:8000/api/news/')
data = r.json()
articles = data if isinstance(data, list) else data.get('results', [])

if articles:
    img_url = articles[0].get('image_url', '')
    if img_url:
        # Test the proxy endpoint
        encoded = urllib.parse.quote(img_url, safe='')
        proxy_url = f'http://localhost:8000/api/news/proxy-image/?url={encoded}'
        
        print(f'Testing proxy with image: {img_url[:60]}...')
        
        try:
            r2 = requests.get(proxy_url, timeout=5)
            print(f'✓ Proxy status: {r2.status_code}')
            print(f'✓ Content-Type: {r2.headers.get("content-type", "N/A")}')
            print(f'✓ Size: {len(r2.content)} bytes')
            print(f'✓ CORS: {r2.headers.get("access-control-allow-origin", "MISSING")}')
        except Exception as e:
            print(f'✗ Error: {e}')
else:
    print('✗ No articles found')
