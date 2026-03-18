#!/usr/bin/env python3
"""Test script using the actual ColesAPI via CDP connection."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from coles_mcp.api import ColesAPI
from coles_mcp.browser import BrowserManager
from coles_mcp.config import load_config


async def test_via_cdp() -> None:
    """Test Coles API using the actual CDP connection."""
    print("=" * 60)
    print("Coles API Test via CDP Connection")
    print("=" * 60)
    print()

    config = load_config()

    print(f"📡 Connecting to Brave CDP on port {config.browser.cdp_port}...")
    browser = BrowserManager(config.browser.cdp_url)

    try:
        page = await browser.get_page()
        print(f"   ✓ Connected to browser")

        # Check current URL
        url = page.url
        print(f"   Current page: {url}")

        # Navigate to Coles if needed
        if "coles.com.au" not in url:
            print(f"\n📄 Navigating to Coles homepage...")
            await page.goto("https://www.coles.com.au", wait_until="domcontentloaded", timeout=30000)
            print(f"   ✓ Navigated to {page.url}")

        # Wait for Incapsula
        print("\n⏳ Waiting for page to stabilize (3 seconds)...")
        await asyncio.sleep(3)

        # Check URL after waiting
        url_after = page.url
        print(f"   Current URL: {url_after}")

        # Create API instance
        api = ColesAPI(page, "")
        api.set_store_context(config.store.store_id, config.store.shopping_method)

        # Try search
        print("\n🔍 Testing product search...")
        result = await api.search("milk")

        if "error" in result:
            print(f"   ✗ Error: {result['error']}")
        else:
            total = result.get("total", 0)
            items = result.get("items", [])
            print(f"   ✓ Search successful!")
            print(f"   Total results: {total}")
            print(f"   Items returned: {len(items)}")

            if items:
                first_item = items[0]
                name = first_item.get("name") or first_item.get("productName", "Unknown")
                price = first_item.get("price") or first_item.get("salePrice", "N/A")
                print(f"   First item: {name} - ${price}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_via_cdp())
