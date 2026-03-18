#!/usr/bin/env python3
"""Test different filter formats for Coles API."""

import asyncio
import sys
import json
from pathlib import Path
from urllib.parse import quote

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def test_filter_formats() -> None:
    """Test different filter formats to find working pattern."""
    print("=" * 60)
    print("Coles API Filter Format Testing")
    print("=" * 60)
    print()

    async with async_playwright() as p:
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        url = "https://www.coles.com.au"

        print(f"📄 Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print("   ✓ Page loaded")

        # Wait for Incapsula
        await asyncio.sleep(5)

        # Set required cookies
        print("🍪 Setting required cookies...")
        await context.add_cookies([
            {"name": "fulfillmentStoreId", "value": "7674", "domain": ".coles.com.au", "path": "/"},
            {"name": "shopping-method", "value": "delivery", "domain": ".coles.com.au", "path": "/"},
        ])
        print("   ✓ Cookies set")

        # Test different filter formats
        subscription_key = "eae83861d1cd4de6bb9cd8a2cd6f041e"
        base_url = "https://www.coles.com.au/api/bff/products/search"

        test_cases = [
            {
                "name": "Empty filters array (current)",
                "filters": "%5B%5D",  # []
            },
            {
                "name": "Empty object in array",
                "filters": "%5B%7B%7D%5D",  # [{}]
            },
            {
                "name": "Special filter all",
                "filters": "%5B%7B%22name%22%3A%22Special%22%2C%22values%22%3A%5B%22all%22%5D%7D%5D",  # [{"name":"Special","values":["all"]}]
            },
            {
                "name": "No filters parameter",
                "filters": None,
            },
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}: {test_case['name']}")

            # Build URL
            if test_case['filters']:
                url = f"{base_url}?storeId=7674&start=0&sortBy=salesDescending&filters={test_case['filters']}&excludeAds=true&authenticated=false&term=milk&subscription-key={subscription_key}"
            else:
                url = f"{base_url}?storeId=7674&start=0&sortBy=salesDescending&excludeAds=true&authenticated=false&term=milk&subscription-key={subscription_key}"

            print(f"   URL: {url[:100]}...")

            try:
                # Use page.evaluate to fetch from browser context
                result = await page.evaluate(f"""
                    async () => {{
                        try {{
                            const resp = await fetch('{url}', {{
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
                            print(f"   ✓ SUCCESS! {total} total products, {len(items)} items")
                            if items:
                                first = items[0]
                                name = first.get("name") or first.get("productName", "Unknown")
                                print(f"   First item: {name}")
                                # We found a working format!
                                print(f"\n   🎯 WORKING FORMAT: {test_case['name']}")
                                break
                        else:
                            print(f"   ⚠️  Got JSON but no items field")
                            print(f"   Keys: {list(data.keys())[:5]}")
                    else:
                        print(f"   ⚠️  Response not JSON")
                        print(f"   Preview: {text[:100]}")
                else:
                    print(f"   ✗ HTTP {result['status']}")
                    print(f"   Response: {result['text'][:100]}")

            except Exception as e:
                print(f"   ✗ Exception: {e}")

        print("\n⏸️ Pausing for 5 seconds...")
        await asyncio.sleep(5)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_filter_formats())