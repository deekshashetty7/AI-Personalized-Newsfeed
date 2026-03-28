import requests
import urllib.parse

# Test with a simple favicon
image_url = 'https://platform.twitter.com/favicon.ico'
encoded_url = urllib.parse.quote(image_url, safe='')

try:
    proxy_url = f'http://localhost:8000/api/news/proxy-image/?url={encoded_url}'
    print(f'Testing proxy with URL: {proxy_url[:80]}...')
    r = requests.get(proxy_url, timeout=5)
    print(f'Proxy request status: {r.status_code}')
    print(f'Content-Type: {r.headers.get("content-type", "unknown")}')
    print(f'Response size: {len(r.content)} bytes')
    print(f'CORS header: {r.headers.get("Access-Control-Allow-Origin", "missing")}')
except Exception as e:
    print(f'Proxy request error: {type(e).__name__}: {str(e)[:200]}')
