#!/usr/bin/env python3
"""Discover subscription key from Coles and test API calls."""

import asyncio
import sys
import json
import re
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def discover_subscription_key() -> str | None:
    """Discover subscription key from Coles website."""
    print("🔍 Discovering subscription key from Coles website...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to Coles
        print("   Navigating to Coles homepage...")
        await page.goto("https://www.coles.com.au", wait_until="domcontentloaded", timeout=30000)

        # Wait for page to load
        await asyncio.sleep(5)

        # Get all script tags
        scripts = await page.evaluate("""() => {
            const scripts = Array.from(document.querySelectorAll('script[src]'));
            return scripts.map(s => s.src).filter(Boolean);
        }""")

        print(f"   Found {len(scripts)} script tags")

        # Pattern for subscription-key in JS
        key_pattern = r'subscription-key["\']?\s*:\s*["\']?([a-f0-9]{32})["\']?'

        # Check first 20 scripts
        for i, script_url in enumerate(scripts[:20], 1):
            if script_url and ".js" in script_url:
                try:
                    print(f"   Checking script {i}/20: {script_url.split('/')[-1][:40]}...")
                    response = await page.evaluate(f"""async () => {{
                        try {{
                            const r = await fetch('{script_url}', {{credentials: 'include'}});
                            const text = await r.text();
                            return text;
                        }} catch(e) {{
                            return null;
                        }}
                    }}""")

                    if response:
                        match = re.search(key_pattern, response, re.IGNORECASE)
                        if match:
                            key = match.group(1)
                            print(f"   ✓ FOUND KEY: {key[:16]}...")
                            await browser.close()
                            return key
                except Exception:
                    continue

        # Check inline scripts
        print("   Checking inline scripts...")
        inline_scripts = await page.evaluate("""() => {
            const scripts = Array.from(document.querySelectorAll('script:not([src])'));
            return scripts.map(s => s.textContent).join('\\n');
        }""")

        if inline_scripts:
            match = re.search(key_pattern, inline_scripts, re.IGNORECASE)
            if match:
                key = match.group(1)
                print(f"   ✓ FOUND KEY in inline scripts: {key[:16]}...")
                await browser.close()
                return key

        print("   ⚠️ No subscription key found")
        await browser.close()
        return None


async def test_with_discovered_key() -> None:
    """Test API calls with discovered or fallback subscription key."""
    print("=" * 60)
    print("Coles API - Subscription Key Discovery & Test")
    print("=" * 60)
    print()

    # Try to discover subscription key
    discovered_key = await discover_subscription_key()

    if discovered_key:
        subscription_key = discovered_key
        print(f"\n✓ Using discovered subscription key: {subscription_key[:16]}...")
    else:
        # Fallback to community research key
        subscription_key = "eae83861d1cd4de6bb9cd8a2cd6f041e"
        print(f"\n⚠️ Using fallback subscription key: {subscription_key[:16]}...")

    # Now test with this key
    print("\n🧪 Testing API call with subscription key...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to Coles first
        print("   Navigating to Coles...")
        await page.goto("https://www.coles.com.au", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        # Set cookies
        await context.add_cookies([
            {"name": "fulfillmentStoreId", "value": "7674", "domain": ".coles.com.au", "path": "/"},
            {"name": "shopping-method", "value": "delivery", "domain": ".coles.com.au", "path": "/"},
        ])

        # Try the API call with different approaches
        test_urls = [
            # Try with no filters
            f"https://www.coles.com.au/api/bff/products/search?storeId=7674&start=0&term=milk&subscription-key={subscription_key}",
            # Try with empty filters array
            f"https://www.coles.com.au/api/bff/products/search?storeId=7674&start=0&filters=%5B%5D&term=milk&subscription-key={subscription_key}",
            # Try with basic parameters
            f"https://www.coles.com.au/api/bff/products/search?storeId=7674&term=milk&subscription-key={subscription_key}",
        ]

        for i, url in enumerate(test_urls, 1):
            print(f"\n   Test {i}: {url[:80]}...")

            try:
                result = await page.evaluate(f"""
                    async () => {{
                        try {{
                            const resp = await fetch('{url}', {{
                                method: 'GET',
                                headers: {{
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json'
                                }},
                                credentials: 'include'
                            }});
                            const status = resp.status;
                            const text = await resp.text();
                            return {{ status, text }};
                        }} catch (e) {{
                            return {{ error: e.message }};
                        }}
                    }}
                """)

                if "error" in result:
                    print(f"   ✗ Fetch error: {result['error']}")
                elif result["status"] == 200:
                    text = result["text"]
                    if text.strip().startswith("{") or text.strip().startswith("["):
                        try:
                            data = json.loads(text)
                            if "items" in data:
                                items = data.get("items", [])
                                total = data.get("total", 0)
                                print(f"   ✓ SUCCESS! {total} products, {len(items)} items")
                                if items:
                                    first = items[0]
                                    name = first.get("name") or first.get("productName", "Unknown")
                                    price = first.get("price") or first.get("salePrice", "N/A")
                                    print(f"   First item: {name} - ${price}")
                                    print(f"\n   🎯 WORKING URL: Test {i}")
                                    break
                                else:
                                    print(f"   ⚠️  Got JSON but no items")
                                    print(f"   Keys: {list(data.keys())[:5]}")
                            else:
                                print(f"   ⚠️  Got JSON but unexpected structure")
                                print(f"   Keys: {list(data.keys())[:5]}")
                        except json.JSONDecodeError:
                            print(f"   ⚠️  Response looks like JSON but failed to parse")
                            print(f"   Preview: {text[:200]}")
                    else:
                        print(f"   ⚠️  Response not JSON")
                        if "<html" in text[:100]:
                            print(f"   Got HTML (Incapsula blocking)")
                        else:
                            print(f"   Preview: {text[:100]}")
                else:
                    print(f"   ✗ HTTP {result['status']}")
                    if result['status'] == 401 or result['status'] == 403:
                        print(f"   ⚠️  Auth failed - subscription key may be invalid")
                    elif result['status'] == 400:
                        print(f"   ⚠️  Bad request - URL parameters may be incorrect")

            except Exception as e:
                print(f"   ✗ Exception: {e}")

        print("\n⏸️ Pausing for 10 seconds...")
        await asyncio.sleep(10)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_with_discovered_key())