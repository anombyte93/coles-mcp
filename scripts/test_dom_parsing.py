#!/usr/bin/env python3
"""Test DOM parsing fallback for Coles search."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright
from coles_mcp.dom_parser import search_via_dom


async def test_dom_parsing() -> None:
    """Test DOM parsing fallback for Coles search."""
    print("=" * 60)
    print("Coles DOM Parsing Test")
    print("=" * 60)
    print()

    async with async_playwright() as p:
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to Coles first
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

        # Test DOM parsing search
        print("\n🔍 Testing DOM parsing search...")
        print("   Query: 'milk'")

        try:
            result = await search_via_dom(page, "milk", "7674")

            if isinstance(result, dict):
                items = result.get("items", [])
                total = result.get("total", 0)

                print(f"\n   ✓ DOM parsing returned {total} products")
                print(f"   ✓ Found {len(items)} items")

                if items:
                    print(f"\n   First 3 items:")
                    for i, item in enumerate(items[:3], 1):
                        name = item.get("name", "Unknown")
                        price = item.get("price", "N/A")
                        print(f"   {i}. {name} - ${price}")
                else:
                    print("   ⚠️ No products found - DOM structure may have changed")
                    print("   Try checking the page visually to see if products loaded")
            else:
                print(f"   ⚠️ Unexpected result type: {type(result)}")

        except Exception as e:
            print(f"   ✗ DOM parsing failed: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")

        print("\n⏸️ Pausing for 10 seconds - check browser visually...")
        await asyncio.sleep(10)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_dom_parsing())