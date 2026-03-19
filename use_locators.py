#!/usr/bin/env python3
"""Use Playwright locators to find products on Coles."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from playwright.async_api import async_playwright
from coles_mcp.config import load_config


async def search_with_locators(query: str) -> list:
    """Search using Playwright's locator API for robust element finding."""

    config = load_config()
    browser_url = config.browser.cdp_url

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(browser_url)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        search_url = f"https://www.coles.com.au/search?q={query}"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        # Wait for React rendering
        print(f"  Waiting for page load...", end=" ")
        await page.wait_for_timeout(10000)

        # Try to find products using various locator strategies
        products = []

        # Strategy 1: Look for any element with price text
        try:
            price_locator = page.locator(":text-match(:\\$\\d+\\.\\d{2})")
            count = await price_locator.count()
            print(f"found {count} price elements")

            if count > 0:
                for i in range(min(count, 20)):  # First 20 prices
                    try:
                        price_text = await price_locator.nth(i).text_content()
                        # Get parent element to find product name
                        parent = await price_locator.nth(i).evaluate("el => el.parentElement.textContent")

                        products.append({
                            'price_text': price_text,
                            'parent_text': parent[:100] if parent else ''
                        })
                    except:
                        continue
        except Exception as e:
            print(f"  Locator error: {e}")

        # Strategy 2: Get all visible text and parse manually
        all_text = await page.evaluate("""() => {
            // Remove header/footer
            const main = document.querySelector('main') || document.body;
            return main.textContent;
        }""")

        # Parse prices from text
        import re
        prices = re.findall(r'\\$\\s*(\\d+)\\.(\\d{2})', all_text)

        print(f"  Found {len(prices)} prices in text")
        if prices:
            print(f"  Sample: ${prices[0][0]}.{prices[0][1]}, ${prices[1][0]}.{prices[1][1] if len(prices) > 1 else ''}")

        # Try to find product names near prices
        # Look for the pattern: Product Name followed by Price
        product_pattern = re.findall(r'([A-Z][A-Za-z\\s\\d]+\\s(?:\\d+g|\\d+ml|\\d+L|kg|pack|punnet))[^$]*\\$(\\d+)\\.(\\d{2})', all_text)

        print(f"  Found {len(product_pattern)} products with prices")

        await browser.close()

        # Format results
        formatted = []
        for name, dollars, cents in product_pattern[:10]:
            formatted.append({
                'name': name.strip(),
                'price': float(f"{dollars}.{cents}")
            })

        return formatted


async def main():
    """Test locator-based extraction."""

    test_queries = ["milk", "bananas"]

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"SEARCH: {query}")
        print('='*80)

        products = await search_with_locators(query)

        if products:
            print(f"\nProducts found:")
            for p in products[:5]:
                print(f"  {p['name']}: ${p['price']:.2f}")
        else:
            print("\nNo products found")


if __name__ == "__main__":
    asyncio.run(main())
