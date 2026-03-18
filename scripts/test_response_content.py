#!/usr/bin/env python3
"""Test script to see actual Coles API response content."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def test_responses() -> None:
    """Test Coles API and see actual response content."""
    print("=" * 60)
    print("Coles API Response Content Analysis")
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

        # Test a simple endpoint
        print("\n🔍 Testing search endpoint...")
        endpoint = "/api/customer/v1/coles/products/search?term=milk"

        try:
            response = await page.request.get(f"https://www.coles.com.au{endpoint}")
            print(f"   Status: {response.status}")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")

            # Get response as text
            text = await response.text()
            print(f"   Response length: {len(text)} characters")
            print(f"   First 500 characters:")
            print("   " + text[:500].replace("\n", "\n   "))

            # Check if it's JSON
            if text.strip().startswith("{") or text.strip().startswith("["):
                print("\n   ✓ Response appears to be JSON")
            elif text.strip().startswith("<"):
                print("\n   ✗ Response is HTML, not JSON")
                print(f"   HTML tag: {text.split('>')[0]}")
            else:
                print(f"\n   ? Unknown format (starts with: {text[:50]})")

        except Exception as e:
            print(f"   ✗ Error: {e}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_responses())
