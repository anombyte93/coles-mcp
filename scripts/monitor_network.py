#!/usr/bin/env python3
"""Monitor network requests to discover actual Coles API endpoints."""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def monitor_network_requests() -> None:
    """Monitor network requests on Coles website to find working API endpoints."""
    print("=" * 60)
    print("Coles Network Request Monitoring")
    print("=" * 60)
    print()

    async with async_playwright() as p:
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Store all API requests
        api_requests = []

        def log_request(request):
            url = request.url
            # Log Coles API calls
            if "coles.com.au" in url and "/api/" in url:
                print(f"\n📡 API Request: {request.method} {url[:100]}")
                api_requests.append({
                    "method": request.method,
                    "url": url,
                    "headers": dict(request.headers),
                })

        def log_response(response):
            url = response.url
            if "coles.com.au" in url and "/api/" in url:
                print(f"   Response: {response.status}")
                print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")

        page.on("request", log_request)
        page.on("response", log_response)

        url = "https://www.coles.com.au"

        print(f"📄 Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print("   ✓ Page loaded")

        # Wait for Incapsula
        print("\n⏳ Waiting for page to stabilize (5 seconds)...")
        await page.wait_for_timeout(5000)

        # Try to trigger a search - look for search input
        print("\n🔍 Attempting to trigger search...")

        # Try to find and interact with search
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
                        await search_box.fill("milk")
                        print("   ✓ Filled 'milk'")
                        await page.wait_for_timeout(2000)

                        # Try to submit or trigger search
                        await page.keyboard.press("Enter")
                        print("   ✓ Pressed Enter")
                        await page.wait_for_timeout(3000)
                        break
                except:
                    continue
            else:
                print("   ⚠️ No search input found")

        except Exception as e:
            print(f"   ⚠️ Search interaction failed: {e}")

        # Check for any API calls captured
        print(f"\n📊 Captured {len(api_requests)} API requests")

        if api_requests:
            print("\n🔑 Analyzing API requests...")

            for i, req in enumerate(api_requests[:10], 1):
                print(f"\n   Request {i}:")
                print(f"   URL: {req['url']}")
                print(f"   Method: {req['method']}")

                # Look for subscription key in headers
                headers = req.get('headers', {})
                sub_key = headers.get('subscription-key') or headers.get('Ocp-Apim-Subscription-Key')
                if sub_key:
                    print(f"   ✓ Subscription Key: {sub_key[:20]}...")

                # Show key headers
                print(f"   Key Headers:")
                for key, value in list(headers.items())[:8]:
                    if key.lower() in ['subscription-key', 'ocp-apim-subscription-key', 'authorization', 'content-type']:
                        print(f"     {key}: {value[:50]}")

        # Try to make a direct API call using captured patterns
        print("\n🌐 Testing direct API call with captured patterns...")

        # Based on research, try BFF format
        test_endpoints = [
            "/api/bff/products/search?term=milk",
            "/api/bff/products?search=milk",
        ]

        subscription_key = "eae8381d1cd4de6bb9cd8a2cd6f041e"

        for endpoint in test_endpoints:
            print(f"\n   Testing: {endpoint}")
            full_url = f"https://www.coles.com.au{endpoint}&subscription-key={subscription_key}"

            try:
                response = await page.request.get(full_url)
                print(f"   Status: {response.status}")

                if response.status == 200:
                    text = await response.text()
                    print(f"   ✓ SUCCESS! Response: {text[:200]}")
                    break
                elif response.status == 500:
                    text = await response.text()
                    print(f"   ⚠️ 500 Error: {text[:200]}")
                else:
                    text = await response.text()
                    print(f"   Response: {text[:100]}")

            except Exception as e:
                print(f"   ✗ Error: {e}")

        print("\n⏸️ Pausing for 10 seconds - check browser visually...")
        await page.wait_for_timeout(10000)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(monitor_network_requests())
