#!/usr/bin/env python3
"""Test script using BFF endpoint from research."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def test_bff_endpoint() -> None:
    """Test Coles BFF endpoint from research."""
    print("=" * 60)
    print("Coles BFF Endpoint Test")
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

        # Test BFF endpoint with subscription key
        print("\n🔍 Testing BFF categories endpoint...")
        subscription_key = "eae83861d1cd4de6bb9cd8a2cd6f041e"
        endpoint = f"/api/bff/products/categories?storeId=0357&subscription-key={subscription_key}"

        print(f"   GET {endpoint[:80]}...")

        try:
            response = await page.request.get(f"https://www.coles.com.au{endpoint}")
            print(f"   Status: {response.status}")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")

            text = await response.text()
            print(f"   Response length: {len(text)} characters")

            if text.strip().startswith("{") or text.strip().startswith("["):
                print("\n   ✓ Response is JSON!")
                print(f"   First 200 characters: {text[:200]}")
            elif "incap" in text.lower():
                print("\n   ✗ Still blocked by Incapsula")
            else:
                print(f"\n   Response preview: {text[:200]}")

        except Exception as e:
            print(f"   ✗ Error: {e}")

        print("\n⏸️ Pausing for 5 seconds...")
        await page.wait_for_timeout(5000)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_bff_endpoint())
