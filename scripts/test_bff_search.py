#!/usr/bin/env python3
"""Test script to find working BFF search endpoint."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def test_bff_search() -> None:
    """Test various BFF search endpoint variations."""
    print("=" * 60)
    print("Coles BFF Search Endpoint Discovery")
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
        print("\n⏳ Waiting for page to stabilize...")
        await page.wait_for_timeout(5000)

        # Set required cookies
        await context.add_cookies([
            {"name": "fulfillmentStoreId", "value": "0357", "domain": ".coles.com.au", "path": "/"},
            {"name": "shopping-method", "value": "delivery", "domain": ".coles.com.au", "path": "/"},
        ])
        print("   ✓ Set required cookies")

        subscription_key = "eae83861d1cd4de6bb9cd8a2cd6f041e"

        # Try different BFF search endpoint variations
        endpoints = [
            f"/api/bff/products/search?term=milk&storeId=0357&subscription-key={subscription_key}",
            f"/api/bff/products/search?query=milk&storeId=0357&subscription-key={subscription_key}",
            f"/api/bff/v1/products/search?term=milk&storeId=0357&subscription-key={subscription_key}",
            f"/api/bff/products?search=milk&storeId=0357&subscription-key={subscription_key}",
        ]

        for endpoint in endpoints:
            print(f"\n🔍 Testing: {endpoint[:60]}...")
            try:
                response = await page.request.get(f"https://www.coles.com.au{endpoint}")
                print(f"   Status: {response.status}")

                text = await response.text()
                if response.status == 200:
                    print(f"   ✓ SUCCESS!")
                    print(f"   First 200 chars: {text[:200]}")
                    break  # Stop if we find a working endpoint
                elif response.status == 500:
                    print(f"   ⚠️ 500 Error (endpoint exists but wrong params)")
                    print(f"   Response: {text[:200]}")
                elif response.status == 404:
                    print(f"   ✗ 404 Not found")
                else:
                    print(f"   Status {response.status}: {text[:100]}")

            except Exception as e:
                print(f"   ✗ Error: {str(e)[:80]}")

        print("\n⏸️ Pausing for 5 seconds...")
        await page.wait_for_timeout(5000)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_bff_search())
