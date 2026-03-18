#!/usr/bin/env python3
"""Test browser automation approach for Coles search."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright
from coles_mcp.browser_tools import search_products_via_browser


async def test_browser_automation() -> None:
    """Test browser automation fallback for Coles search."""
    print("=" * 60)
    print("Coles Browser Automation Test")
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

        # Set cookies
        print("🍪 Setting required cookies...")
        await context.add_cookies([
            {"name": "fulfillmentStoreId", "value": "7674", "domain": ".coles.com.au", "path": "/"},
            {"name": "shopping-method", "value": "delivery", "domain": ".coles.com.au", "path": "/"},
        ])
        print("   ✓ Cookies set")

        # Test browser automation search
        print("\n🔍 Testing browser automation search...")
        print("   Query: 'milk'")

        try:
            result = await search_products_via_browser(page, "milk", "7674")

            if isinstance(result, dict):
                items = result.get("items", [])
                total = result.get("total", 0)

                print(f"\n   Result: {total} products found, {len(items)} items")

                if items:
                    print(f"\n   First 3 items:")
                    for i, item in enumerate(items[:3], 1):
                        name = item.get("name", "Unknown")
                        price = item.get("price", "N/A")
                        print(f"   {i}. {name} - ${price}")

                    print(f"\n   ✓✓✓ SUCCESS! Browser automation found products!")
                    print(f"   This approach WORKS - tools can function via browser automation")
                else:
                    print(f"   ⚠️ No products found")
                    print(f"   Checking page content...")

                    # Check what's actually on the page
                    page_text = await page.evaluate("""() => {
                        return document.body.innerText.substring(0, 500);
                    }""")

                    print(f"   Page preview: {page_text[:200]}")

                    if "Pardon Our Interruption" in page_text or "Incapsula" in page_text or "Imperva" in page_text:
                        print(f"   ❌ Page blocked by anti-bot protection")
                    else:
                        print(f"   ⚠️ Page loaded but no products found")

        except Exception as e:
            print(f"   ✗ Browser automation failed: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")

        print("\n⏸️ Pausing for 10 seconds - check browser visually...")
        await asyncio.sleep(10)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_browser_automation())