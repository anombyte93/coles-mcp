#!/usr/bin/env python3
"""Debug script to see what URL is being constructed."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def debug_url_construction() -> None:
    """Debug URL construction for Coles API."""
    print("=" * 60)
    print("URL Construction Debug")
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
        await page.wait_for_timeout(3000)

        # Test different URL formats
        test_urls = [
            "https://www.coles.com.au/api/customer/v1/coles/products/search?term=milk",
            "https://www.coles.com.au/api/customer/v1/coles/products/search/?term=milk",
            "https://www.coles.com.au/api/digital/v1/coles/products/search?queryString=milk&storeId=0357",
        ]

        for test_url in test_urls:
            print(f"\n🔍 Testing: {test_url}")
            try:
                response = await page.request.get(test_url)
                print(f"   Status: {response.status}")

                text = await response.text()
                if text.strip().startswith("{"):
                    print(f"   ✓ JSON response!")
                    print(f"   First 100 chars: {text[:100]}")
                elif "incap" in text.lower():
                    print(f"   ✗ Incapsula blocked")
                else:
                    print(f"   Response: {text[:100]}")
            except Exception as e:
                print(f"   ✗ Error: {e}")

        print("\n⏸️ Pausing for 5 seconds...")
        await page.wait_for_timeout(5000)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_url_construction())
