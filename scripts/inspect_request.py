#!/usr/bin/env python3
"""Inspect actual Coles API request format during real user interaction."""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def inspect_actual_request() -> None:
    """Monitor actual API calls during real user interaction on Coles."""
    print("=" * 60)
    print("Coles API Request Inspector")
    print("=" * 60)
    print()

    async with async_playwright() as p:
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Store all API request details
        api_requests = []

        def log_request(request):
            url = request.url
            # Log Coles API calls
            if "coles.com.au" in url and "/api/" in url and "search" in url:
                print(f"\n📡 API Request: {request.method}")
                print(f"   URL: {url}")

                # Parse query parameters
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(url)
                params = parse_qs(parsed.query)

                print(f"   Query Parameters:")
                for key, value in params.items():
                    if isinstance(value, list):
                        print(f"     {key}: {value[0]}")
                    else:
                        print(f"     {key}: {value}")

                # Log headers
                headers = dict(request.headers)
                print(f"   Key Headers:")
                for key in ['subscription-key', 'ocp-apim-subscription-key', 'content-type', 'accept']:
                    if key in headers:
                        print(f"     {key}: {headers[key][:50]}")

                api_requests.append({
                    "url": url,
                    "method": request.method,
                    "headers": headers,
                    "params": params
                })

        def log_response(response):
            url = response.url
            if "coles.com.au" in url and "/api/" in url and "search" in url:
                print(f"   Response: {response.status}")
                content_type = response.headers.get('content-type', 'N/A')
                print(f"   Content-Type: {content_type}")

        page.on("request", log_request)
        page.on("response", log_response)

        url = "https://www.coles.com.au"

        print(f"📄 Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print("   ✓ Page loaded")

        # Wait for Incapsula
        print("\n⏳ Waiting for page to stabilize...")
        await asyncio.sleep(5)

        # Set required cookies
        print("\n🍪 Setting required cookies...")
        await context.add_cookies([
            {"name": "fulfillmentStoreId", "value": "7674", "domain": ".coles.com.au", "path": "/"},
            {"name": "shopping-method", "value": "delivery", "domain": ".coles.com.au", "path": "/"},
        ])
        print("   ✓ Cookies set (storeId: 7674)")

        # Try to trigger a search by looking for search input and interacting
        print("\n🔍 Attempting to trigger search via UI...")

        try:
            # Look for search input
            search_selectors = [
                'input[placeholder*="search" i]',
                'input[aria-label*="search" i]',
                'input[type="search"]',
                'input[name="search"]',
                '[data-testid*="search" i]',
            ]

            for selector in search_selectors:
                try:
                    search_box = page.locator(selector).first
                    if await search_box.count() > 0:
                        print(f"   ✓ Found search input: {selector}")

                        # Fill in search term
                        await search_box.fill("milk")
                        print("   ✓ Filled 'milk'")

                        await asyncio.sleep(2)

                        # Try to submit or trigger search
                        await page.keyboard.press("Enter")
                        print("   ✓ Pressed Enter")

                        # Wait for results to load
                        await asyncio.sleep(5)
                        break
                except:
                    continue
            else:
                print("   ⚠️ No search input found, trying direct navigation")

                # Try navigating directly to search results URL
                search_url = "https://www.coles.com.au/search?q=milk"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(5)

        except Exception as e:
            print(f"   ⚠️ Search interaction failed: {e}")

        # Check captured requests
        print(f"\n📊 Captured {len(api_requests)} search API requests")

        if api_requests:
            print("\n🔑 Analyzing captured request format...")

            for i, req in enumerate(api_requests[:3], 1):  # Show first 3
                print(f"\n   Request {i}:")
                print(f"   URL: {req['url']}")

                # Show the clean URL structure
                from urllib.parse import urlparse, parse_qs, urlencode

                parsed = urlparse(req['url'])
                params = parse_qs(parsed.query)

                print(f"   Base path: {parsed.path}")
                print(f"   Parameters:")
                for key, value in params.items():
                    if isinstance(value, list):
                        print(f"     {key}: {value[0]}")

                # Show headers
                headers = req.get('headers', {})
                sub_key = headers.get('subscription-key') or headers.get('ocp-apim-subscription-key')
                if sub_key:
                    print(f"   ✓ Subscription Key: {sub_key[:20]}...")

            # Save the first complete request for reference
            if api_requests:
                first_req = api_requests[0]
                print(f"\n💾 Saving request details to /tmp/coles_api_request.json")
                with open("/tmp/coles_api_request.json", "w") as f:
                    json.dump(first_req, f, indent=2)
        else:
            print("\n⚠️ No API requests captured. UI interaction may not have triggered search.")

        print("\n⏸️ Pausing for 10 seconds - check browser visually...")
        await asyncio.sleep(10)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(inspect_actual_request())