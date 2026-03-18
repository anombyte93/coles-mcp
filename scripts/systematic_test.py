#!/usr/bin/env python3
"""Systematic test of different approaches to make Coles API work."""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def systematic_test() -> None:
    """Test different approaches systematically."""
    print("=" * 60)
    print("Coles API Systematic Testing")
    print("=" * 60)
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Test approaches
        approaches = [
            {
                "name": "Navigate then wait 10s then API",
                "nav_wait": 10,
                "use_cookies": True,
            },
            {
                "name": "Navigate then wait 30s then API",
                "nav_wait": 30,
                "use_cookies": True,
            },
            {
                "name": "Navigate to search page then API",
                "nav_to_search": True,
                "use_cookies": True,
            },
        ]

        subscription_key = "eae83861d1cd4de6bb9cd8a2cd6f041e"

        for approach in approaches:
            print(f"\n🧪 Testing: {approach['name']}")
            print("-" * 40)

            try:
                # Navigate to Coles
                await page.goto("https://www.coles.com.au", wait_until="domcontentloaded", timeout=30000)
                print("   ✓ Navigated to Coles")

                # Set cookies if needed
                if approach.get('use_cookies'):
                    await context.add_cookies([
                        {"name": "fulfillmentStoreId", "value": "7674", "domain": ".coles.com.au", "path": "/"},
                        {"name": "shopping-method", "value": "delivery", "domain": ".coles.com.au", "path": "/"},
                    ])
                    print("   ✓ Cookies set")

                # Navigate to search if needed
                if approach.get('nav_to_search'):
                    await page.goto("https://www.coles.com.au/search?q=milk", wait_until="domcontentloaded", timeout=30000)
                    print("   ✓ Navigated to search page")

                # Wait specified time
                wait_time = approach.get('nav_wait', 0)
                if wait_time > 0:
                    print(f"   ⏳ Waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)

                # Try API call
                url = f"https://www.coles.com.au/api/bff/products/search?storeId=7674&start=0&term=milk&subscription-key={subscription_key}"
                print(f"   📡 Calling API...")

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
                    print(f"   ✗ Error: {result['error']}")
                elif result["status"] == 200:
                    text = result["text"]
                    if text.strip().startswith("{") or text.strip().startswith("["):
                        try:
                            data = json.loads(text)
                            if "items" in data:
                                items = data.get("items", [])
                                total = data.get("total", 0)
                                print(f"   ✓✓✓ SUCCESS! {total} products, {len(items)} items")
                                if items:
                                    first = items[0]
                                    name = first.get("name") or first.get("productName", "Unknown")
                                    price = first.get("price") or first.get("salePrice", "N/A")
                                    print(f"   First item: {name} - ${price}")
                                print(f"\n   🎯🎯🎯 WINNING APPROACH: {approach['name']}")
                                break
                            else:
                                print(f"   ⚠️  Got JSON but no items")
                                print(f"   Keys: {list(data.keys())[:5]}")
                        except json.JSONDecodeError:
                            print(f"   ⚠️  JSON parse error")
                            print(f"   Preview: {text[:200]}")
                    else:
                        print(f"   ⚠️  Not JSON (got HTML)")
                        if "<html" in text[:100]:
                            print(f"   Incapsula blocking detected")
                else:
                    print(f"   ✗ HTTP {result['status']}")

            except Exception as e:
                print(f"   ✗ Exception: {e}")

        print("\n" + "=" * 60)
        print("Testing complete. If no approach worked, Incapsula is blocking.")
        print("=" * 60)

        print("\n⏸️ Pausing for 5 seconds...")
        await asyncio.sleep(5)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(systematic_test())