#!/usr/bin/env python3
"""
Server API Explorer
Discovers available API endpoints on the FashionXG server
"""

import requests
from bs4 import BeautifulSoup

server_url = "http://45.249.246.186:5000"

print(f"🔍 Exploring FashionXG Server API")
print(f"Server: {server_url}")
print("=" * 60)
print()

# Get homepage
try:
    response = requests.get(server_url, timeout=10)
    if response.status_code == 200:
        print("✅ Server is accessible")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print()

        # Try to parse HTML to find links
        if 'html' in response.headers.get('content-type', ''):
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all links
            links = soup.find_all('a', href=True)
            if links:
                print("Found links on homepage:")
                for link in links[:20]:  # Show first 20 links
                    href = link['href']
                    text = link.get_text(strip=True)
                    print(f"  - {href} ({text})")
                print()

        # Show first 500 chars of response
        print("Homepage preview:")
        print(response.text[:500])
        print()

except Exception as e:
    print(f"❌ Error accessing server: {e}")
    print()

# Try common Flask routes
print("\nTrying common Flask routes:")
print("-" * 60)

routes = [
    '/api/images',
    '/images',
    '/gallery',
    '/data',
    '/pending',
    '/processed',
    '/feedback',
    '/tags',
]

for route in routes:
    try:
        response = requests.get(f"{server_url}{route}", timeout=5)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} {route}: {response.status_code}")
    except Exception as e:
        print(f"❌ {route}: Error")

print()
print("=" * 60)
print("Note: The server might be using Flask with different route structure.")
print("Check the server code to find the actual API endpoints.")
