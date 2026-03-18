#!/usr/bin/env python3
"""Test script that waits for Incapsula challenge to complete."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def test_with_incapsula() -> None:
    """Test Coles API after letting Incapsula challenge complete."""
    print("=" * 60)
    print("Coles API with Incapsula Challenge")
    print("=" * 60)
    print()

    async with async_playwright() as p:
        print("🌐 Launching browser (headed)...")
        # Use headed mode to see Incapsula challenge
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        url = "https://www.coles.com.au"

        print(f"📄 Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print("   ✓ Page loaded")

        # Wait for Incapsula challenge to complete
        print("\n⏳ Waiting for Incapsula challenge (5 seconds)...")
        await page.wait_for_timeout(5000)

        # Check if we're still on Incapsula page
        current_url = page.url
        print(f"   Current URL: {current_url}")

        if "incap" in current_url.lower() or "challenge" in current_url.lower():
            print("   ⚠️ Still on Incapsula challenge page")
            print("   Waiting another 5 seconds...")
            await page.wait_for_timeout(5000)

            current_url = page.url
            print(f"   Current URL: {current_url}")

        # Check cookies now
        print("\n🍪 Checking cookies after Incapsula...")
        cookies = await context.cookies()
        print(f"   Found {len(cookies)} cookies")

        cookie_names = [c["name"] for c in cookies]
        print(f"   Cookie names: {', '.join(cookie_names[:15])}")

        # Look for Coles-specific cookies
        coles_cookies = [c for c in cookies if "cole" in c["name"].lower()]
        if coles_cookies:
            print(f"\n   ✓ Found Coles cookies: {[c['name'] for c in coles_cookies]}")
        else:
            print("\n   ⚠️ No Coles-specific cookies found (still Incapsula-protected)")

        # Set required cookies
        await context.add_cookies([
            {"name": "fulfillmentStoreId", "value": "0357", "domain": ".coles.com.au", "path": "/"},
            {"name": "shopping-method", "value": "delivery", "domain": ".coles.com.au", "path": "/"},
        ])
        print("\n   ✓ Set required cookies (fulfillmentStoreId, shopping-method)")

        # Test API call
        print("\n🔍 Testing search endpoint...")
        endpoint = "/api/customer/v1/coles/products/search?term=milk"

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
                print(f"\n   ? Response: {text[:200]}")

        except Exception as e:
            print(f"   ✗ Error: {e}")

        print("\n⏸️ Pausing for 10 seconds - check browser visually...")
        await page.wait_for_timeout(10000)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_with_incapsula())
