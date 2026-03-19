#!/usr/bin/env python3
"""Search Coles for specific items and extract prices."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from coles_mcp.browser import BrowserManager
from coles_mcp.config import load_config
from coles_mcp.api import ColesAPI


async def search_item(api: ColesAPI, query: str) -> dict | None:
    """Search for a single item and return first result."""
    try:
        result = await api.search(query, page_num=1)

        if "error" in result:
            return None

        items = result.get("items", [])
        if not items:
            return None

        first = items[0]
        return {
            "query": query,
            "name": first.get("name", "N/A"),
            "price": first.get("price", 0),
            "sale_price": first.get("salePrice", first.get("price", 0)),
            "listed_price": first.get("listedPrice", first.get("price", 0)),
            "unit_price": first.get("unitPrice", "N/A"),
            "url": first.get("url", ""),
        }
    except Exception as e:
        print(f"  Error searching for '{query}': {e}")
        return None


async def main():
    """Search for all shopping list items."""
    print("=" * 80)
    print("Coles Price Lookup - Shopping List")
    print("=" * 80)

    config = load_config()
    browser = BrowserManager(config.browser.cdp_url)
    page = await browser.get_page()
    api = ColesAPI(page, config.api.subscription_key)
    api.set_store_context(config.store.store_id, config.store.shopping_method)

    shopping_list = [
        "Lotus Biscoff Biscuit",
        "YoPRO High Protein Yoghurt Strawberry",
        "Brown onions 1kg bag",
        "Frozen mixed berries organic",
        "Chicken breast fillet",
        "Lean beef mince 1kg",
        "Strawberries punnet",
        "Nectarines",
        "Rockmelon",
        "Sweet potato gold",
        "Wicked Sister rice pudding",
        "D'Orsogna mild salami",
        "Whipped cream",
        "Bananas",
    ]

    results = []

    for query in shopping_list:
        print(f"\n🔍 Searching: {query}...")
        result = await search_item(api, query)
        if result:
            results.append(result)
            print(f"  ✓ Found: {result['name'][:60]}")
            print(f"    Price: ${result['sale_price']:.2f}")
        else:
            print(f"  ✗ Not found")
            results.append({"query": query, "name": "NOT FOUND", "price": 0, "unit_price": "N/A"})

    # Print table
    print("\n" + "=" * 80)
    print("PRICE TABLE")
    print("=" * 80)
    print(f"{'Item':<40} {'Price':>10} {'Unit Price':>15}")
    print("-" * 80)

    for r in results:
        name = r['name'][:38] + ".." if len(r['name']) > 40 else r['name']
        price = f"${r['price']:.2f}" if r['price'] > 0 else "N/A"
        unit_price = str(r['unit_price'])[:13]
        print(f"{name:<40} {price:>10} {unit_price:>15}")

    # Calculate total
    total = sum(r['price'] for r in results if r['price'] > 0)
    print("-" * 80)
    print(f"{'ESTIMATED TOTAL':<40} {'':>10} ${total:.2f}")
    print("=" * 80)

    # Note about data source
    print("\nNote: Prices from Coles website. May vary by store/location.")
    print("Unit prices shown where available.")


if __name__ == "__main__":
    asyncio.run(main())
