#!/usr/bin/env python3
"""Test API calls after navigating to search page."""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def test_with_navigation() -> None:
    """Test API calls after proper navigation to search results."""
    print("=" * 60)
    print("Coles API - Navigation Context Test")
    print("=" * 60)
    print()

    async with async_playwright() as p:
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Capture API calls during navigation
        api_calls = []

        def log_response(response):
            if "coles.com.au" in response.url and "/api/" in response.url:
                print(f"\n📡 API Call Detected: {response.status}")
                print(f"   URL: {response.url[:80]}...")

                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        print(f"   ✓ JSON response!")
                        api_calls.append({
                            "url": response.url,
                            "status": response.status,
                            "content_type": content_type
                        })

        page.on("response", log_response)

        # Navigate to Coles homepage first
        url = "https://www.coles.com.au"
        print(f"📄 Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print("   ✓ Page loaded")

        # Wait for page stabilization
        print("⏳ Waiting for page to stabilize...")
        await asyncio.sleep(5)

        # Set required cookies
        print("🍪 Setting required cookies...")
        await context.add_cookies([
            {"name": "fulfillmentStoreId", "value": "7674", "domain": ".coles.com.au", "path": "/"},
            {"name": "shopping-method", "value": "delivery", "domain": ".coles.com.au", "path": "/"},
        ])
        print("   ✓ Cookies set")

        # Try different navigation approaches
        test_approaches = [
            {
                "name": "Direct search URL navigation",
                "action": "navigate_search",
                "url": "https://www.coles.com.au/search?q=milk"
            },
            {
                "name": "Using search box if found",
                "action": "search_box",
                "query": "milk"
            },
        ]

        for approach in test_approaches:
            print(f"\n🧪 Testing: {approach['name']}")

            if approach['action'] == 'navigate_search':
                try:
                    await page.goto(approach['url'], wait_until="domcontentloaded", timeout=30000)
                    print(f"   ✓ Navigated to search page")
                    await asyncio.sleep(5)

                    # Check if we captured any API calls
                    if api_calls:
                        print(f"   ✓ Captured {len(api_calls)} API calls during navigation")
                        break
                except Exception as e:
                    print(f"   ✗ Navigation failed: {e}")

            elif approach['action'] == 'search_box':
                try:
                    # Try to find search input
                    search_selectors = [
                        'input[placeholder*="search" i]',
                        'input[aria-label*="search" i]',
                        'input[type="search"]',
                        '[data-testid*="search" i]',
                        '#search',
                    ]

                    for selector in search_selectors:
                        try:
                            search_box = page.locator(selector).first
                            if await search_box.count() > 0:
                                print(f"   ✓ Found search input: {selector}")

                                await search_box.fill(approach['query'])
                                print(f"   ✓ Filled '{approach['query']}'")
                                await asyncio.sleep(1)

                                await page.keyboard.press("Enter")
                                print(f"   ✓ Pressed Enter")

                                await asyncio.sleep(5)

                                if api_calls:
                                    print(f"   ✓ Captured {len(api_calls)} API calls")
                                    break
                        except:
                            continue

                    if api_calls:
                        break

                except Exception as e:
                    print(f"   ✗ Search box interaction failed: {e}")

        # Analyze captured API calls
        if api_calls:
            print(f"\n📊 Analysis: Captured {len(api_calls)} working API calls")

            for i, call in enumerate(api_calls[:3], 1):
                print(f"\n   API Call {i}:")
                print(f"   URL: {call['url']}")

                # Extract the URL structure
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(call['url'])
                params = parse_qs(parsed.query)

                print(f"   Base: {parsed.path}")
                print(f"   Params:")
                for key, value in params.items():
                    if isinstance(value, list) and value:
                        print(f"     {key}: {value[0][:50]}")
        else:
            print(f"\n⚠️ No API calls captured. Trying manual fetch...")

            # Try manual fetch after navigation
            subscription_key = "eae83861d1cd4de6bb9cd8a2cd6f041e"
            test_url = f"https://www.coles.com.au/api/bff/products/search?storeId=7674&start=0&sortBy=salesDescending&filters=%5B%5D&excludeAds=true&authenticated=false&term=milk&subscription-key={subscription_key}"

            print(f"   Testing fetch to: {test_url[:80]}...")

            result = await page.evaluate(f"""
                async () => {{
                    try {{
                        const resp = await fetch('{test_url}', {{
                            method: 'GET',
                            headers: {{
                                'Content-Type': 'application/json',
                                'Accept': 'application/json'
                            }},
                            credentials: 'include'
                        }});
                        const status = resp.status;
                        const text = await resp.text();
                        return {{ status, text }};
                    }} catch (e) {{
                        return {{ error: e.message }};
                    }}
                }}
            """)

            if "error" in result:
                print(f"   ✗ Fetch error: {result['error']}")
            elif result["status"] == 200:
                text = result["text"]
                if text.strip().startswith("{"):
                    data = json.loads(text)
                    if "items" in data:
                        items = data.get("items", [])
                        total = data.get("total", 0)
                        print(f"   ✓ SUCCESS! {total} products, {len(items)} items")
                        if items:
                            first = items[0]
                            name = first.get("name") or first.get("productName", "Unknown")
                            print(f"   First item: {name}")
                    else:
                        print(f"   ⚠️  Got JSON but unexpected format")
                        print(f"   Keys: {list(data.keys())[:5]}")
                else:
                    print(f"   ⚠️  Response not JSON")
                    print(f"   Preview: {text[:100]}")
            else:
                print(f"   ✗ HTTP {result['status']}")
                print(f"   Preview: {result['text'][:100]}")

        print("\n⏸️ Pausing for 10 seconds - check browser visually...")
        await asyncio.sleep(10)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_with_navigation())