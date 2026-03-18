#!/usr/bin/env python3
"""Test script using captured actual Coles API endpoint."""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def test_captured_endpoint() -> None:
    """Test using captured Coles API endpoint."""
    print("=" * 60)
    print("Coles API - Captured Endpoint Test")
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
        await page.wait_for_timeout(5000)

        # Set required cookies
        await context.add_cookies([
            {"name": "fulfillmentStoreId", "value": "7674", "domain": ".coles.com.au", "path": "/"},
            {"name": "shopping-method", "value": "delivery", "domain": ".coles.com.au", "path": "/"},
        ])
        print("   ✓ Set required cookies")

        # Test the captured endpoint format
        print("\n🔍 Testing captured endpoint format...")

        # Endpoint captured from network monitoring
        endpoint = "/api/bff/products/search?storeId=7674&start=0&sortBy=salesDescending&filters=%5B%7B%22name%22%3A%22Special%22%2C%22values%22%3A%5B%22all%22%5D%7D%5D&excludeAds=true&authenticated=false&term=milk"

        print(f"   GET {endpoint[:80]}...")

        try:
            response = await page.request.get(f"https://www.coles.com.au{endpoint}")
            print(f"   Status: {response.status}")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")

            text = await response.text()

            if response.status == 200:
                print(f"   Response length: {len(text)} characters")

                if text.strip().startswith("{"):
                    print("\n   ✓ Response is JSON!")
                    try:
                        data = json.loads(text)
                        print(f"   Keys: {list(data.keys())[:10]}")

                        # Look for items
                        if "items" in data:
                            items = data.get("items", [])
                            print(f"   ✓ Found {len(items)} items")
                            if items:
                                first = items[0]
                                name = first.get("name") or first.get("productName", "Unknown")
                                price = first.get("price") or first.get("salePrice", "N/A")
                                print(f"   First item: {name} - ${price}")
                    except json.JSONDecodeError as e:
                        print(f"   ✗ JSON parse error: {e}")
                        print(f"   Response preview: {text[:200]}")
                else:
                    print(f"   Response preview: {text[:200]}")

        except Exception as e:
            print(f"   ✗ Error: {e}")

        print("\n⏸️ Pausing for 5 seconds...")
        await page.wait_for_timeout(5000)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_captured_endpoint())
