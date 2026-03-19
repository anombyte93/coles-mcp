#!/usr/bin/env python3
"""Test Coles MCP tools against the live Coles website."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from coles_mcp.browser import BrowserManager
from coles_mcp.config import load_config
from coles_mcp.api import ColesAPI


async def test_health_check() -> dict:
    """Test 1: Health check - verifies CDP, API, auth, subscription key."""
    print("\n🔍 TEST 1: coles_health_check")
    print("-" * 50)

    try:
        config = load_config()
        browser = BrowserManager(config.browser.cdp_url)
        page = await browser.get_page()
        api = ColesAPI(page, config.api.subscription_key)
        api.set_store_context(config.store.store_id, config.store.shopping_method)

        result = await api.health_check()
        print(f"✅ CDP: {result.get('cdp', {}).get('status')}")
        print(f"✅ API: {result.get('api', {}).get('status')}")
        print(f"✅ Auth: {result.get('auth', {}).get('status')}")
        print(f"✅ Subscription Key: {result.get('subscription_key', {}).get('status')}")

        if result.get('subscription_key', {}).get('status') == 'ok':
            key = result.get('subscription_key', {}).get('key', 'N/A')
            print(f"   Key: {key[:20]}...{key[-10:]}")

        return {"test": "health_check", "status": "pass" if result.get('cdp', {}).get('status') == 'ok' else "fail", "result": result}
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return {"test": "health_check", "status": "fail", "error": str(e)}


async def test_search() -> dict:
    """Test 2: Search for products."""
    print("\n🔍 TEST 2: coles_search(query='milk')")
    print("-" * 50)

    try:
        config = load_config()
        browser = BrowserManager(config.browser.cdp_url)
        page = await browser.get_page()
        api = ColesAPI(page, config.api.subscription_key)
        api.set_store_context(config.store.store_id, config.store.shopping_method)

        result = await api.search("milk", page_num=1)

        if "error" in result:
            print(f"❌ API ERROR: {result['error']}")
            return {"test": "search", "status": "fail", "error": result['error']}

        items = result.get("items", [])
        print(f"✅ Found {len(items)} products")
        print(f"✅ Total results: {result.get('total', 0)}")

        if items:
            first = items[0]
            print(f"\n   First product:")
            print(f"   - Name: {first.get('name', 'N/A')}")
            print(f"   - Price: ${first.get('price', 0)}")
            print(f"   - ID: {first.get('id', 'N/A')}")

        return {"test": "search", "status": "pass" if items else "partial", "result": result}
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return {"test": "search", "status": "fail", "error": str(e)}


async def test_specials() -> dict:
    """Test 3: Browse specials."""
    print("\n🔍 TEST 3: coles_specials()")
    print("-" * 50)

    try:
        config = load_config()
        browser = BrowserManager(config.browser.cdp_url)
        page = await browser.get_page()
        api = ColesAPI(page, config.api.subscription_key)
        api.set_store_context(config.store.store_id, config.store.shopping_method)

        result = await api.specials(category_id="", page_num=1)

        if "error" in result:
            print(f"❌ API ERROR: {result['error']}")
            return {"test": "specials", "status": "fail", "error": result['error']}

        items = result.get("items", [])
        print(f"✅ Found {len(items)} special items")
        print(f"✅ Total specials: {result.get('total', 0)}")

        if items:
            first = items[0]
            print(f"\n   First special:")
            print(f"   - Name: {first.get('name', 'N/A')}")
            print(f"   - Price: ${first.get('price', 0)}")
            print(f"   - Was: ${first.get('wasPrice', 'N/A')}")

        return {"test": "specials", "status": "pass" if items else "partial", "result": result}
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return {"test": "specials", "status": "fail", "error": str(e)}


async def test_product_detail() -> dict:
    """Test 4: Get product details."""
    print("\n🔍 TEST 4: coles_product_detail()")
    print("-" * 50)

    try:
        config = load_config()
        browser = BrowserManager(config.browser.cdp_url)
        page = await browser.get_page()
        api = ColesAPI(page, config.api.subscription_key)
        api.set_store_context(config.store.store_id, config.store.shopping_method)

        # First search to get a product ID
        search_result = await api.search("milk", page_num=1)
        if "error" in search_result or not search_result.get("items"):
            return {"test": "product_detail", "status": "skip", "reason": "No products from search"}

        product_id = str(search_result["items"][0]["id"])
        print(f"   Testing with product ID: {product_id}")

        result = await api.product_detail(product_id)

        if "error" in result:
            print(f"❌ API ERROR: {result['error']}")
            return {"test": "product_detail", "status": "fail", "error": result['error']}

        print(f"✅ Product: {result.get('name', 'N/A')}")
        print(f"✅ Price: ${result.get('price', 0)}")
        print(f"✅ Brand: {result.get('brand', 'N/A')}")
        print(f"✅ Size: {result.get('size', 'N/A')}")
        print(f"✅ Description: {result.get('description', 'N/A')[:80]}...")

        return {"test": "product_detail", "status": "pass", "result": result}
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return {"test": "product_detail", "status": "fail", "error": str(e)}


async def main():
    """Run all live tests."""
    print("=" * 50)
    print("Coles MCP - Live API Verification")
    print("=" * 50)

    results = []

    # Test 1: Health Check
    result = await test_health_check()
    results.append(result)

    if result["status"] == "fail":
        print("\n⚠️  Health check failed - stopping tests")
        print("   Brave CDP may not be running on port 61000")
        return

    # Test 2: Search
    result = await test_search()
    results.append(result)

    # Test 3: Specials
    result = await test_specials()
    results.append(result)

    # Test 4: Product Detail
    result = await test_product_detail()
    results.append(result)

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    passed = sum(1 for r in results if r["status"] == "pass")
    partial = sum(1 for r in results if r["status"] == "partial")
    failed = sum(1 for r in results if r["status"] == "fail")

    print(f"✅ Passed: {passed}")
    print(f"⚠️  Partial: {partial}")
    print(f"❌ Failed: {failed}")

    for r in results:
        status_icon = "✅" if r["status"] == "pass" else "⚠️" if r["status"] == "partial" else "❌"
        print(f"   {status_icon} {r['test']}: {r['status']}")


if __name__ == "__main__":
    asyncio.run(main())
