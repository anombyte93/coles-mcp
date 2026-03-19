#!/usr/bin/env python3
"""Extract prices using Playwright accessibility snapshot."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from playwright.async_api import async_playwright
from coles_mcp.config import load_config


async def search_with_accessibility(query: str) -> list:
    """Search using accessibility tree for better product extraction."""

    config = load_config()
    browser_url = config.browser.cdp_url

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(browser_url)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        search_url = f"https://www.coles.com.au/search?q={query}"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        # Wait for React rendering
        await page.wait_for_timeout(8000)

        # Get accessibility snapshot
        snapshot = await page.accessibility.snapshot()

        # Extract products from accessibility tree
        products = extract_products_from_tree(snapshot)

        await browser.close()
        return products


def extract_products_from_tree(node, depth=0, products=None):
    """Recursively extract products from accessibility tree."""
    if products is None:
        products = []

    # Look for product-like nodes
    if node.get('role') in ['listitem', 'article', 'link']:
        name = node.get('name', '')
        if name and len(name) > 10 and len(name) < 200:
            # This might be a product
            products.append({
                'name': name,
                'role': node.get('role'),
                'depth': depth
            })

    # Recurse into children
    for child in node.get('children', []):
        extract_products_from_tree(child, depth + 1, products)

    return products


async def search_with_text_extraction(query: str) -> dict:
    """Search using intelligent text extraction."""

    config = load_config()
    browser_url = config.browser.cdp_url

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(browser_url)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        search_url = f"https://www.coles.com.au/search?q={query}"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        # Wait for React rendering
        await page.wait_for_timeout(8000)

        # Extract using more specific selectors
        content = await page.evaluate("""() => {
            const results = [];

            // Look for all text nodes that contain prices
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );

            let node;
            const products = [];

            while (node = walker.nextNode()) {
                const text = node.textContent.trim();
                if (text.includes('$') && text.match(/\$\d+\.\d{2}/)) {
                    // Found a price, try to find associated product name
                    let parent = node.parentElement;
                    let attempts = 0;
                    let productName = '';

                    while (parent && attempts < 5) {
                        // Look for text before the price that might be the product name
                        const siblings = parent.parentElement?.children || [];
                        for (const sibling of siblings) {
                            if (sibling !== parent && sibling.textContent) {
                                const siblingText = sibling.textContent.trim();
                                if (siblingText && siblingText.length > 10 && siblingText.length < 100
                                    && !siblingText.includes('$') && !siblingText.includes('Add')) {
                                    productName = siblingText.split('\\n')[0].trim();
                                    break;
                                }
                            }
                        }

                        if (productName) break;
                        parent = parent.parentElement;
                        attempts++;
                    }

                    products.push({
                        name: productName || 'Unknown Product',
                        price: text,
                        raw: text
                    });
                }
            }

            return {
                query: window.location.search,
                products: products.slice(0, 10)
            };
        }""")

        await browser.close()
        return content


async def main():
    """Extract prices for all shopping list items."""

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
    print("Coles Price Lookup")
    print("=" * 90)

    results = []

    for original_query, search_query in shopping_list:
        print(f"\n🔍 {original_query}...", end=" ")

        try:
            content = await search_with_text_extraction(search_query)
            products = content.get('products', [])

            if products:
                # Use first product
                first = products[0]
                name = first['name']
                price_text = first['price']

                # Parse price
                import re
                match = re.search(r'\$(\d+)\.(\d{2})', price_text)
                if match:
                    price = float(f"{match.group(1)}.{match.group(2)}")
                    results.append({
                        'name': name,
                        'price': price,
                        'unit_price': 'N/A'
                    })
                    print(f"✓ ${price:.2f}")
                else:
                    results.append({'name': name, 'price': 0, 'unit_price': 'N/A'})
                    print(f"? {price_text}")
            else:
                results.append({'name': 'NOT FOUND', 'price': 0, 'unit_price': 'N/A'})
                print(f"✗ Not found")

        except Exception as e:
            results.append({'name': 'ERROR', 'price': 0, 'unit_price': 'N/A'})
            print(f"✗ Error: {e}")

        await asyncio.sleep(1)  # Rate limiting

    # Print table
    print("\n" + "=" * 90)
    print("PRICE TABLE")
    print("=" * 90)
    print(f"{'Item':<50} {'Price':>12}")
    print("-" * 90)

    for r in results:
        name = r['name'][:48] + ".." if len(r.get('name', '')) > 50 else r.get('name', 'NOT FOUND')
        price = f"${r['price']:.2f}" if r['price'] > 0 else "N/A"
        print(f"{name:<50} {price:>12}")

    total = sum(r['price'] for r in results if r['price'] > 0)
    found_count = sum(1 for r in results if r['price'] > 0)
    print("-" * 90)
    print(f"{'ESTIMATED TOTAL':<50} {'':>12} ${total:.2f}")
    print(f"{'Found':<50} {found_count:>12} of {len(results)} items")
    print("=" * 90)


if __name__ == "__main__":
    asyncio.run(main())
