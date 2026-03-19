#!/usr/bin/env python3
"""Extract prices using Playwright accessibility tree."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from playwright.async_api import async_playwright
from coles_mcp.config import load_config


async def search_with_accessibility(query: str):
    """Extract products using accessibility tree."""

    config = load_config()
    browser_url = config.browser.cdp_url

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(browser_url)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        search_url = f"https://www.coles.com.au/search?q={query}"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        # Wait for React to fully render
        await page.wait_for_timeout(12000)

        # Get full accessibility tree
        snapshot = await page.accessibility.snapshot()

        # Extract products
        products = extract_from_tree(snapshot)

        await browser.close()
        return products


def extract_from_tree(node, products=None):
    """Extract products from accessibility tree."""
    if products is None:
        products = []

    # Look for list items or articles that might be products
    if node.get('role') in ['listitem', 'article', 'link']:
        name = node.get('name', '')

        # Check if it has a price
        if '$' in name and name.count('$') == 1:
            # This might be a product with price
            parts = name.rsplit('$', 1)
            if len(parts) == 2:
                product_name = parts[0].strip()
                price_part = parts[1].strip()

                # Try to parse price
                try:
                    # Price might be like "3.20" or "3.20 each" or "3.20 / 100g"
                    price_match = price_part.split()[0]
                    price = float(price_match)

                    if 0.50 < price < 500:  # Sanity check
                        products.append({
                            'name': product_name,
                            'price': price
                        })
                except:
                    pass

    # Recurse
    for child in node.get('children', []):
        extract_from_tree(child, products)

    return products


async def main():
    """Extract all shopping list prices."""

    shopping_list = [
        ("Lotus Biscoff Biscuit", "Lotus Biscoff"),
        ("YoPRO High Protein Yoghurt Strawberry", "YoPRO Strawberry"),
        ("Brown onions 1kg bag", "Brown onions"),
        ("Frozen mixed berries organic", "Organic mixed berries"),
        ("Chicken breast fillet", "Chicken breast"),
        ("Lean beef mince 1kg", "Lean beef mince"),
        ("Strawberries punnet", "Strawberries"),
        ("Nectarines", "Nectarines"),
        ("Rockmelon", "Rockmelon"),
        ("Sweet potato gold", "Sweet potato"),
        ("Wicked Sister rice pudding", "Wicked Sister rice pudding"),
        ("D'Orsogna mild salami", "D'Orsogna salami"),
        ("Whipped cream", "Whipped cream"),
        ("Bananas", "Bananas"),
    ]

    print("=" * 90)
    print("Coles Price Lookup - Using Accessibility Tree")
    print("=" * 90)

    results = []

    for original_query, search_query in shopping_list:
        print(f"\n🔍 {original_query}...", end=" ", flush=True)

        try:
            products = await search_with_accessibility(search_query)

            if products:
                # Use first product
                first = products[0]
                results.append({
                    'name': first['name'],
                    'price': first['price']
                })
                print(f"✓ ${first['price']:.2f}")
            else:
                results.append({'name': 'NOT FOUND', 'price': 0})
                print(f"✗ Not found")

        except Exception as e:
            results.append({'name': 'ERROR', 'price': 0})
            print(f"✗ Error: {str(e)[:50]}")

        await asyncio.sleep(2)  # Rate limiting

    # Print table
    print("\n" + "=" * 90)
    print("PRICE TABLE")
    print("=" * 90)
    print(f"{'Item':<50} {'Price':>12} {'Unit Price':>15}")
    print("-" * 90)

    for r in results:
        name = r['name'][:48] + ".." if len(r.get('name', '')) > 50 else r.get('name', 'NOT FOUND')
        price = f"${r['price']:.2f}" if r['price'] > 0 else "N/A"
        unit_price = "N/A"  # Not easily accessible
        print(f"{name:<50} {price:>12} {unit_price:>15}")

    total = sum(r['price'] for r in results if r['price'] > 0)
    found_count = sum(1 for r in results if r['price'] > 0)
    print("-" * 90)
    print(f"{'ESTIMATED TOTAL':<50} {'':>12} ${total:.2f}")
    print(f"{'Found':<50} {found_count:>12} of {len(results)} items")
    print("=" * 90)
    print("\nNote: Prices from Coles website. Unit prices require detailed product pages.")


if __name__ == "__main__":
    asyncio.run(main())
