#!/usr/bin/env python3
"""Improved price extraction from Coles website."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from playwright.async_api import async_playwright
from coles_mcp.config import load_config


async def search_and_extract(query: str) -> dict | None:
    """Navigate to Coles search and extract product data with better price parsing."""

    config = load_config()
    browser_url = config.browser.cdp_url

    async with async_playwright() as p:
        # Connect to existing Brave CDP
        browser = await p.chromium.connect_over_cdp(browser_url)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to search
        search_url = f"https://www.coles.com.au/search?q={query}"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        # Wait for products to load
        await page.wait_for_timeout(3000)

        # Extract product data with improved price parsing
        products = await page.evaluate("""() => {
            const items = [];

            // Try multiple product card selectors
            const cards = document.querySelectorAll('[data-testid="product-item"], .product-card, [class*="ProductCard"]');

            cards.forEach(card => {
                // Extract name
                const nameEl = card.querySelector('[class*="name"], [class*="title"], h3, h4, a[aria-label]');
                const name = nameEl?.textContent?.trim() || nameEl?.getAttribute('aria-label') || '';

                if (!name) return;

                // Extract price - try multiple selectors
                let priceText = '';
                let unitPriceText = '';

                // Method 1: Look for price in dollar format
                const priceSelectors = [
                    '[class*="price"]',
                    '[class*="Price"]',
                    '.dollars',
                    '.cents',
                    '[data-testid="price"]',
                ];

                for (const selector of priceSelectors) {
                    const el = card.querySelector(selector);
                    if (el) {
                        const text = el.textContent?.trim() || '';
                        if (text.includes('$') || text.match(/\d+\.\d{2}/)) {
                            priceText = text;
                            break;
                        }
                    }
                }

                // Method 2: Look for separate dollars and cents
                if (!priceText) {
                    const dollars = card.querySelector('.dollars, [class*="dollar"]');
                    const cents = card.querySelector('.cents, [class*="cent"]');
                    if (dollars && cents) {
                        priceText = `$${dollars.textContent.trim()}.${cents.textContent.trim()}`;
                    }
                }

                // Method 3: Look for any text with price pattern
                if (!priceText) {
                    const allText = card.textContent || '';
                    const priceMatch = allText.match(/\$(\d+)\.(\d{2})/);
                    if (priceMatch) {
                        priceText = `$${priceMatch[1]}.${priceMatch[2]}`;
                    }
                }

                // Extract unit price
                const unitPriceEl = card.querySelector('[class*="unit"], [class*="Unit"]');
                unitPriceText = unitPriceEl?.textContent?.trim() || '';

                // Parse price
                let price = 0;
                if (priceText) {
                    const match = priceText.match(/\$(\d+)\.(\d{2})/);
                    if (match) {
                        price = parseFloat(`${match[1]}.${match[2]}`);
                    }
                }

                if (name && price > 0) {
                    items.push({
                        name: name,
                        price: price,
                        priceText: priceText,
                        unitPrice: unitPriceText
                    });
                }
            });

            return items;
        }""")

        await browser.close()

        if products and len(products) > 0:
            return {
                "query": query,
                "name": products[0]["name"],
                "price": products[0]["price"],
                "price_text": products[0]["priceText"],
                "unit_price": products[0]["unitPrice"],
            }
        return None


async def main():
    """Search for all items with improved price extraction."""

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

    print("=" * 90)
    print("Coles Price Lookup - Shopping List")
    print("=" * 90)

    results = []

    for query in shopping_list:
        print(f"\n🔍 {query}...", end=" ")
        result = await search_and_extract(query)
        if result:
            results.append(result)
            print(f"✓ ${result['price']:.2f}")
        else:
            print("✗ Not found")
            results.append({"query": query, "name": "NOT FOUND", "price": 0, "unit_price": "N/A"})

    # Print table
    print("\n" + "=" * 90)
    print("PRICE TABLE")
    print("=" * 90)
    print(f"{'Item':<50} {'Price':>12} {'Unit Price':>20}")
    print("-" * 90)

    for r in results:
        name = r['name'][:48] + ".." if len(r.get('name', '')) > 50 else r.get('name', 'NOT FOUND')
        price = f"${r['price']:.2f}" if r['price'] > 0 else "N/A"
        unit_price = str(r.get('unit_price', 'N/A'))[:18]
        print(f"{name:<50} {price:>12} {unit_price:>20}")

    # Calculate total
    total = sum(r['price'] for r in results if r['price'] > 0)
    found_count = sum(1 for r in results if r['price'] > 0)
    print("-" * 90)
    print(f"{'ESTIMATED TOTAL':<50} {'':>12} ${total:.2f}")
    print(f"{'Found':<50} {found_count:>12} of {len(results)} items")
    print("=" * 90)

    print("\nNote: Prices may vary by store/location and availability.")


if __name__ == "__main__":
    asyncio.run(main())
