#!/usr/bin/env python3
"""Test script to find the correct Coles API endpoints."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def test_endpoints() -> None:
    """Test various Coles API endpoints to find the correct ones."""
    print("=" * 60)
    print("Coles API Endpoint Discovery")
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

        # Set required cookies
        await context.add_cookies([
            {"name": "fulfillmentStoreId", "value": "0357", "domain": ".coles.com.au", "path": "/"},
            {"name": "shopping-method", "value": "delivery", "domain": ".coles.com.au", "path": "/"},
        ])
        print("   ✓ Set required cookies")

        # Try different endpoint variations
        endpoints = [
            # Plan document examples
            ("/api/bff/products/categories?storeId=0357", "Plan doc example 1"),
            ("/api/customer/v1/coles/products/search/?term=milk", "Plan doc example 2"),
            ("/api/customer/v1/coles/products/search?term=milk", "Without trailing slash"),
            ("/api/digital/v1/coles/products/search?queryString=milk&storeId=0357", "Digital API format"),
            # Common variations
            ("/apis/ui/products/search?term=milk", "Woolies-style path"),
            ("/_api/products/search?q=milk", "Underscore API"),
        ]

        print("\n🔍 Testing different endpoint variations...")

        for endpoint, description in endpoints:
            print(f"\n{description}:")
            print(f"   GET {endpoint}")

            try:
                response = await page.request.get(f"https://www.coles.com.au{endpoint}")
                print(f"   Status: {response.status}")

                if response.status == 200:
                    print(f"   ✓ SUCCESS!")
                    data = await response.json()
                    print(f"   Response keys: {list(data.keys())[:10]}")
                elif response.status in [401, 403]:
                    print(f"   ✗ Auth required")
                    text = await response.text()
                    if "subscription" in text.lower() or "key" in text.lower():
                        print(f"   Response mentions subscription/key: {text[:200]}")
                elif response.status == 404:
                    print(f"   ✗ Not found")
                else:
                    text = await response.text()
                    print(f"   Response: {text[:200]}")

            except Exception as e:
                print(f"   ✗ Error: {str(e)[:100]}")

        # Try with subscription key parameter
        print("\n🔑 Testing with subscription key parameter...")
        test_key = "eae83861d1cd4de6bb9cd8a2cd6f041e"  # Example from plan doc

        endpoints_with_key = [
            (f"/api/bff/products/categories?storeId=0357&subscription-key={test_key}", "Plan doc with key"),
            (f"/api/customer/v1/coles/products/search/?term=milk&subscription-key={test_key}", "Search with key"),
        ]

        for endpoint, description in endpoints_with_key:
            print(f"\n{description}:")
            print(f"   GET {endpoint[:80]}...")

            try:
                response = await page.request.get(f"https://www.coles.com.au{endpoint}")
                print(f"   Status: {response.status}")

                if response.status == 200:
                    print(f"   ✓ SUCCESS!")
                    data = await response.json()
                    print(f"   Response: {str(data)[:200]}")
                else:
                    text = await response.text()
                    print(f"   Response: {text[:200]}")

            except Exception as e:
                print(f"   ✗ Error: {str(e)[:100]}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_endpoints())
