#!/usr/bin/env python3
"""Diagnose Coles API response structure."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from coles_mcp.browser import BrowserManager
from coles_mcp.config import load_config
from coles_mcp.api import ColesAPI


async def main():
    print("=" * 60)
    print("Coles API Response Diagnostics")
    print("=" * 60)

    config = load_config()
    browser = BrowserManager(config.browser.cdp_url)
    page = await browser.get_page()
    api = ColesAPI(page, config.api.subscription_key)
    api.set_store_context(config.store.store_id, config.store.shopping_method)

    # Test 1: Health check details
    print("\n🔍 Health Check Response:")
    print("-" * 60)
    health = await api.health_check()
    print(json.dumps(health, indent=2))

    # Test 2: Search response structure
    print("\n🔍 Search Response Structure (first 3 items):")
    print("-" * 60)
    search_result = await api.search("milk", page_num=1)

    if "items" in search_result and search_result["items"]:
        for i, item in enumerate(search_result["items"][:3]):
            print(f"\nItem {i+1}:")
            print(f"  Keys: {list(item.keys())}")
            print(f"  ID field: {item.get('id', 'MISSING')}")
            print(f"  Name: {item.get('name', 'N/A')}")
            print(f"  Price: {item.get('price', 'N/A')}")

            # Check for alternative ID fields
            if "id" not in item:
                print("  ⚠️  Looking for alternative ID fields...")
                for key in item.keys():
                    if "id" in key.lower():
                        print(f"    Found: {key} = {item[key]}")
    else:
        print(f"Error: {search_result.get('error', 'Unknown error')}")

    # Test 3: Check what the API expects for product detail
    print("\n🔍 API Product Detail Call (with hardcoded ID):")
    print("-" * 60)

    # Try with a common Coles product ID format
    test_ids = ["123456", "6087180", "6129010P"]  # Various Coles ID formats

    for test_id in test_ids:
        print(f"\nTrying ID: {test_id}")
        try:
            detail = await api.product_detail(test_id)
            if "error" in detail:
                print(f"  ❌ Error: {detail['error']}")
            else:
                print(f"  ✅ Success!")
                print(f"  Name: {detail.get('name', 'N/A')}")
        except Exception as e:
            print(f"  ❌ Exception: {e}")


if __name__ == "__main__":
    asyncio.run(main())
