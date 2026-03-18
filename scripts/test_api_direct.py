#!/usr/bin/env python3
"""Test script to make direct API calls to Coles and see what's required."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def test_api_direct() -> None:
    """Test direct API calls to Coles to understand requirements."""
    print("=" * 60)
    print("Coles API Direct Test")
    print("=" * 60)
    print()

    async with async_playwright() as p:
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        url = "https://www.coles.com.au"

        print(f"📄 Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print("   ✓ Page loaded")

        # Get cookies after page load
        print("\n🍪 Checking cookies...")
        cookies = await context.cookies()
        print(f"   Found {len(cookies)} cookies")

        # Look for specific cookies
        cookie_names = [c["name"] for c in cookies]
        print(f"   Cookie names: {', '.join(cookie_names[:10])}")

        # Try to make a search API call
        print("\n🔍 Testing search API call...")

        # First, let's see what API calls the page makes
        print("\n📡 Monitoring network requests...")

        api_requests = []

        def log_request(request):
            url = request.url
            if "api.coles.com.au" in url:
                print(f"   API Request: {request.method} {url[:80]}")
                api_requests.append({"method": request.method, "url": url, "headers": request.headers})

        page.on("request", log_request)

        # Trigger a search on the page
        try:
            search_input = page.locator("input[type='search'], input[placeholder*='search' i], input[aria-label*='search' i]").first
            await search_input.fill("milk")
            await page.wait_for_timeout(2000)  # Wait for debounce
            print("   ✓ Filled search input")
        except Exception as e:
            print(f"   ✗ Could not fill search input: {e}")

        # Wait a bit for API calls
        await page.wait_for_timeout(3000)

        print(f"\n📊 Captured {len(api_requests)} API requests")

        if api_requests:
            print("\n🔑 First API request details:")
            req = api_requests[0]
            print(f"   URL: {req['url']}")
            print(f"   Method: {req['method']}")
            print("\n   Headers:")
            for key, value in list(req["headers"].items())[:10]:
                if key.lower() in ["subscription-key", "ocp-apim-subscription-key", "authorization"]:
                    print(f"   ✓ {key}: {value[:20]}..." if len(value) > 20 else f"   ✓ {key}: {value}")
                elif key.lower() != "cookie":
                    print(f"     {key}: {value[:50]}")

        # Try making a direct API call
        print("\n🌐 Attempting direct API call...")

        try:
            # Try the search endpoint
            search_url = "https://api.coles.com.au/digital/v1/coles/products/search?queryString=milk&storeId=0357"

            response = await page.request.get(search_url)
            print(f"   Status: {response.status}")

            if response.status == 401:
                print("   ✗ 401 Unauthorized - subscription key required")
                print("\n   Response headers:")
                headers = response.headers
                for key, value in headers.items():
                    print(f"     {key}: {value}")
            elif response.status == 200:
                print("   ✓ 200 OK - API call succeeded!")
                data = await response.json()
                print(f"   Found {len(data.get('items', []))} results")
            else:
                print(f"   Status {response.status}")
                text = await response.text()
                print(f"   Response: {text[:200]}")

        except Exception as e:
            print(f"   ✗ Error: {e}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_api_direct())
