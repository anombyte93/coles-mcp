#!/usr/bin/env python3
"""Test Coles API calls through CDP connection with browser session state."""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright
from coles_mcp.api import ColesAPI


async def test_cdp_session() -> None:
    """Test Coles API through CDP connection with proper session state."""
    print("=" * 60)
    print("Coles API - CDP Session Test")
    print("=" * 60)
    print()

    async with async_playwright() as p:
        print("🌐 Connecting to Brave CDP on slot 5 (port 61005)...")

        # Connect to existing Brave CDP instance
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:61005")
            print("   ✓ Connected to CDP")
        except Exception as e:
            print(f"   ✗ CDP connection failed: {e}")
            print("   Make sure Brave is running with CDP on port 61005")
            print("   Run: launch-brave-cdp 5")
            return

        # Get or create context
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
            print("   ✓ Using existing browser context")
        else:
            context = await browser.new_context()
            print("   ✓ Created new browser context")

        # Get or create page
        pages = context.pages
        if pages:
            page = pages[0]
            print("   ✓ Using existing page")
        else:
            page = await context.new_page()
            print("   ✓ Created new page")

        # Initialize ColesAPI with the page
        print("\n🔧 Initializing ColesAPI...")
        api = ColesAPI(page)
        print("   ✓ ColesAPI initialized")

        # Navigate to Coles homepage first (important for session state)
        print("\n📄 Navigating to Coles homepage...")
        try:
            await page.goto("https://www.coles.com.au", wait_until="domcontentloaded", timeout=30000)
            print("   ✓ Page loaded")

            # Wait for page to stabilize
            await asyncio.sleep(3)
            print("   ✓ Page stabilized (3s delay)")
        except Exception as e:
            print(f"   ✗ Navigation failed: {e}")
            return

        # Set required cookies
        print("\n🍪 Setting required cookies...")
        await context.add_cookies([
            {"name": "fulfillmentStoreId", "value": "7674", "domain": ".coles.com.au", "path": "/"},
            {"name": "shopping-method", "value": "delivery", "domain": ".coles.com.au", "path": "/"},
        ])
        api.set_store_context("7674", "delivery")
        print("   ✓ Cookies set (storeId: 7674)")

        # Test health check first
        print("\n🏥 Testing health_check...")
        try:
            health = await api.health_check()
            print(f"   CDP: {health.get('cdp', {}).get('status', 'unknown')}")
            print(f"   API: {health.get('api', {}).get('status', 'unknown')}")
            print(f"   Auth: {health.get('auth', {}).get('status', 'unknown')}")
            print(f"   Subscription Key: {health.get('subscription_key', {}).get('status', 'unknown')}")
        except Exception as e:
            print(f"   ✗ Health check failed: {e}")

        # Test search with the updated endpoint
        print("\n🔍 Testing search with updated endpoint...")
        print("   Query: 'milk'")
        print("   Store: 7674")

        try:
            result = await api.search("milk", page_num=1, page_size=5)

            if result.get("error"):
                error_code = result.get("error")
                message = result.get("message", "Unknown error")
                print(f"   ✗ API returned error: {error_code} - {message}")

                # Check if it's an auth error (subscription key issue)
                if error_code in {401, 403}:
                    print("   ⚠️  This is an auth error - subscription key may be invalid")
            elif isinstance(result, dict):
                # Check if we got valid JSON response
                if "items" in result:
                    items = result.get("items", [])
                    total = result.get("total", 0)
                    print(f"   ✓ SUCCESS! Found {total} total products")
                    print(f"   ✓ Returned {len(items)} items in this page")

                    if items:
                        first = items[0]
                        name = first.get("name") or first.get("productName", "Unknown")
                        price = first.get("price") or first.get("salePrice", "N/A")
                        print(f"\n   First item:")
                        print(f"   - Name: {name}")
                        print(f"   - Price: ${price}")
                else:
                    # Got JSON but unexpected structure
                    print(f"   ⚠️  Got JSON but unexpected structure")
                    print(f"   Keys: {list(result.keys())[:10]}")
                    print(f"   Preview: {json.dumps(result)[:200]}...")
            else:
                print(f"   ⚠️  Unexpected response type: {type(result)}")
                print(f"   Response: {result}")

        except Exception as e:
            print(f"   ✗ Search failed with exception: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")

        # Keep browser open for inspection
        print("\n⏸️ Pausing for 10 seconds - check browser for visual inspection...")
        await asyncio.sleep(10)

        # Don't close browser - leave it running for further testing
        print("\n✓ Test complete. Browser left open for further testing.")


if __name__ == "__main__":
    asyncio.run(test_cdp_session())