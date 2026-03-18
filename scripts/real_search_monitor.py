#!/usr/bin/env python3
"""Monitor actual API calls during real user search on Coles."""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def monitor_real_search() -> None:
    """Monitor API calls during real user search interaction."""
    print("=" * 60)
    print("Coles Real Search Monitoring")
    print("=" * 60)
    print()
    print("This script will:")
    print("1. Navigate to Coles")
    print("2. Wait for you to manually perform a search")
    print("3. Capture the exact API calls made during your search")
    print()

    async with async_playwright() as p:
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Store all API calls
        api_calls = []

        def log_request(request):
            url = request.url
            if "coles.com.au" in url and "/api/" in url:
                print(f"\n📡 API Request: {request.method}")
                print(f"   URL: {url[:120]}...")

                # Log headers
                headers = dict(request.headers)
                sub_key = headers.get('subscription-key') or headers.get('ocp-apim-subscription-key')
                if sub_key:
                    print(f"   Subscription Key: {sub_key[:20]}...")

                # Log body for POST requests
                if request.method == "POST":
                    try:
                        post_data = request.post_data
                        if post_data:
                            print(f"   Body: {post_data[:100]}...")
                    except:
                        pass

        def log_response(response):
            url = response.url
            if "coles.com.au" in url and "/api/" in url:
                print(f"   Response: {response.status}")
                content_type = response.headers.get('content-type', 'N/A')
                print(f"   Content-Type: {content_type}")

                if response.status == 200 and 'application/json' in content_type:
                    print(f"   ✓ JSON response!")

                    # Try to get response body
                    try:
                        # Get response body
                        body = response.body()
                        if body:
                            data = json.loads(body)
                            if "items" in data:
                                items = data.get("items", [])
                                total = data.get("total", 0)
                                print(f"   ✓ Found {total} products, {len(items)} items")

                                if items:
                                    first = items[0]
                                    name = first.get("name") or first.get("productName", "Unknown")
                                    price = first.get("price") or first.get("salePrice", "N/A")
                                    print(f"   First item: {name} - ${price}")

                            api_calls.append({
                                "url": url,
                                "status": response.status,
                                "data": data
                            })
                    except Exception as e:
                        print(f"   (Could not parse response body: {e})")

        page.on("request", log_request)
        page.on("response", log_response)

        # Navigate to Coles
        url = "https://www.coles.com.au"
        print(f"\n📄 Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print("   ✓ Page loaded")

        # Set cookies
        print("\n🍪 Setting required cookies...")
        await context.add_cookies([
            {"name": "fulfillmentStoreId", "value": "7674", "domain": ".coles.com.au", "path": "/"},
            {"name": "shopping-method", "value": "delivery", "domain": ".coles.com.au", "path": "/"},
        ])
        print("   ✓ Cookies set")

        print("\n" + "=" * 60)
        print("👆 NOW: Perform a search in the browser window")
        print("   - Type 'milk' in the search box")
        print("   - Press Enter or click search")
        print("   - Wait for results to load")
        print("=" * 60)
        print("\nWaiting for API calls...")

        # Wait for user to perform search (60 seconds)
        for i in range(60):
            await asyncio.sleep(1)
            if api_calls:
                print(f"\n✓ Captured {len(api_calls)} working API calls!")
                break
            if i % 10 == 0 and i > 0:
                print(f"   Waiting... ({i}s)")

        # Analyze captured calls
        if api_calls:
            print("\n" + "=" * 60)
            print("📊 ANALYSIS: Working API Call Format")
            print("=" * 60)

            for i, call in enumerate(api_calls[:3], 1):
                print(f"\nAPI Call {i}:")
                print(f"URL: {call['url']}")

                # Extract URL structure
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(call['url'])
                params = parse_qs(parsed.query)

                print(f"Base path: {parsed.path}")
                print(f"Parameters:")
                for key, value in params.items():
                    if isinstance(value, list) and value:
                        val = value[0]
                        if len(val) > 50:
                            val = val[:50] + "..."
                        print(f"  {key}: {val}")

                # Show response structure
                data = call.get('data', {})
                if data:
                    print(f"Response structure:")
                    print(f"  Keys: {list(data.keys())[:10]}")

            # Save the working example
            if api_calls:
                working_call = api_calls[0]
                print(f"\n💾 Saving working API call to /tmp/coles_working_api.json")
                with open("/tmp/coles_working_api.json", "w") as f:
                    json.dump(working_call, f, indent=2)
        else:
            print("\n⚠️ No API calls captured within 60 seconds")
            print("   Make sure to perform a search in the browser window!")

        print("\n⏸️ Pausing for 10 seconds for final inspection...")
        await asyncio.sleep(10)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(monitor_real_search())