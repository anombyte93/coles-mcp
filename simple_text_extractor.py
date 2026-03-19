#!/usr/bin/env python3
"""Simple text-based extraction from Coles search pages."""

import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from playwright.async_api import async_playwright
from coles_mcp.config import load_config


async def extract_prices_simple(query: str):
    """Extract prices using simple text content parsing."""

    config = load_config()
    browser_url = config.browser.cdp_url

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(browser_url)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        search_url = f"https://www.coles.com.au/search?q={query}"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        # Wait for React rendering
        await page.wait_for_timeout(12000)

        # Get ALL text content
        all_text = await page.evaluate("""() => {
            return document.body.textContent;
        }""")

        await browser.close()

        # Parse product names and prices from text
        # Pattern: Product Name followed by $X.XX
        products = []

        # Split by lines and look for product patterns
        lines = all_text.split('\\n')

        for i, line in enumerate(lines):
            line = line.strip()

            # Look for lines with prices
            price_match = re.search(r'\\$([0-9]+)\\.([0-9]{2})', line)

            if price_match:
                price = float(f"{price_match.group(1)}.{price_match.group(2)}")

                # Look backwards for product name
                # Check previous lines for a product name
                product_name = "Unknown"
                for j in range(max(0, i-5), i):
                    prev_line = lines[j].strip()
                    # Product names are typically 10-100 chars, contain letters/numbers
                    if 10 < len(prev_line) < 150 and prev_line[0].isupper():
                        product_name = prev_line
                        break

                # Clean up product name
                product_name = re.sub(r'\\s+', ' ', product_name)
                product_name = product_name.split('Add')[0].strip()  # Remove "Add to cart" text

                if len(product_name) > 5 and 0.50 < price < 500:
                    products.append({
                        'name': product_name,
                        'price': price
                    })

        # Remove duplicates
        seen = set()
        unique_products = []
        for p in products:
            key = f"{p['name']}|{p['price']}"
            if key not in seen:
                seen.add(key)
                unique_products.append(p)

        return unique_products[:10]  # Return first 10


async def main():
    """Extract prices for all items."""

    shopping_list = [
        ("Lotus Biscoff Biscuit", "Lotus Biscoff"),
        ("YoPRO High Protein Yoghurt Strawberry", "YoPRO Strawberry yoghurt"),
        ("Brown onions 1kg bag", "Brown onions"),
        ("Frozen mixed berries organic", "Organic mixed berries frozen"),
        ("Chicken breast fillet", "Chicken breast fillet"),
        ("Lean beef mince 1kg", "Lean beef mince"),
        ("Strawberries punnet", "Strawberries punnet"),
        ("Nectarines", "Nectarines"),
        ("Rockmelon", "Rockmelon"),
        ("Sweet potato gold", "Sweet potato gold"),
        ("Wicked Sister rice pudding", "Wicked Sister rice pudding"),
        ("D'Orsogna mild salami", "D'Orsogna salami"),
        ("Whipped cream", "Whipped cream"),
        ("Bananas", "Bananas"),
    ]

    print("=" * 100)
    print("Coles Price Lookup")
    print("=" * 100)

    results = []

    for original_query, search_query in shopping_list:
        print(f"\\n🔍 {original_query}...", end=" ", flush=True)

        try:
            products = await extract_prices_simple(search_query)

            if products:
                first = products[0]
                results.append({
                    'name': first['name'],
                    'price': first['price']
                })
                print(f"✓ ${first['price']:.2f} - {first['name'][:40]}")
            else:
                results.append({'name': 'NOT FOUND', 'price': 0})
                print(f"✗ Not found")

        except Exception as e:
            results.append({'name': 'ERROR', 'price': 0})
            print(f"✗ {str(e)[:40]}")

        await asyncio.sleep(2)

    # Print table
    print("\\n" + "=" * 100)
    print("PRICE TABLE")
    print("=" * 100)
    print(f"{'Item':<55} {'Price':>12} {'Unit Price':>20}")
    print("-" * 100)

    for r in results:
        name = r['name'][:53] + ".." if len(r.get('name', '')) > 55 else r.get('name', 'NOT FOUND')
        price = f"${r['price']:.2f}" if r['price'] > 0 else "N/A"
        unit_price = "N/A"
        print(f"{name:<55} {price:>12} {unit_price:>20}")

    total = sum(r['price'] for r in results if r['price'] > 0)
    found_count = sum(1 for r in results if r['price'] > 0)
    print("-" * 100)
    print(f"{'ESTIMATED TOTAL':<55} {'':>12} ${total:.2f}")
    print(f"{'Found':<55} {found_count:>12} of {len(results)} items")
    print("=" * 100)
    print("\\n⚠️  Prices may vary by store/location. Unit prices not available in search results.")


if __name__ == "__main__":
    asyncio.run(main())
