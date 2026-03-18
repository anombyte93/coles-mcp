#!/usr/bin/env python3
"""Test script to see what fetch URL is actually being used."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def test_fetch_url() -> None:
    """Test what fetch URL is actually constructed."""
    print("=" * 60)
    print("Fetch URL Construction Test")
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

        # Test fetch with URL logging
        print("\n🔍 Testing fetch with URL logging...")

        js = """
        async () => {
            const testUrl = 'https://www.coles.com.au/api/customer/v1/coles/products/search?term=milk';
            console.log('Fetching:', testUrl);

            try {
                const resp = await fetch(testUrl, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    credentials: 'include'
                });

                console.log('Response status:', resp.status);
                console.log('Response headers:', Object.fromEntries(resp.headers.entries()));

                if (!resp.ok) {
                    return { error: resp.status, message: resp.statusText };
                }

                const text = await resp.text();
                console.log('Response length:', text.length);
                console.log('Response preview:', text.substring(0, 200));

                // Try to parse as JSON
                try {
                    const json = JSON.parse(text);
                    return json;
                } catch (e) {
                    return { error: 'not_json', text: text.substring(0, 500) };
                }
            } catch (e) {
                return { error: 'fetch_failed', message: e.message };
            }
        }
        """

        result = await page.evaluate(js)

        if "error" in result:
            print(f"   ✗ Error: {result['error']}")
            if "text" in result:
                print(f"   Response text: {result['text']}")
        else:
            print(f"   ✓ Success!")
            print(f"   Result type: {type(result)}")
            print(f"   Result: {str(result)[:500]}")

        print("\n⏸️ Pausing for 5 seconds...")
        await page.wait_for_timeout(5000)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_fetch_url())
