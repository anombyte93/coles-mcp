#!/usr/bin/env python3
"""Diagnose what's actually on Coles search pages."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from playwright.async_api import async_playwright
from coles_mcp.config import load_config


async def diagnose_search_page(query: str):
    """See what's actually rendered on the search page."""

    config = load_config()
    browser_url = config.browser.cdp_url

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(browser_url)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        search_url = f"https://www.coles.com.au/search?q={query}"
        print(f"Loading: {search_url}")
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        # Wait for page to settle
        await page.wait_for_timeout(5000)

        print(f"Final URL: {page.url}")
        print(f"Page title: {page.title()}")

        # Check if we're being blocked
        is_blocked = "incapsula" in page.url.lower() or "blocked" in page.url.lower()
        print(f"Blocked by Incapsula: {is_blocked}")

        if is_blocked:
            print("\n⚠️  PAGE IS BLOCKED - Can't extract data")
            return

        # What's on the page?
        page_text = await page.evaluate("""() => {
            return {
                bodyText: document.body?.textContent?.substring(0, 500),
                productCards: document.querySelectorAll('[data-testid="product-item"], .product-card').length,
                allDivs: document.querySelectorAll('div').length,
                hasPrice: !!document.querySelector('[class*="price"]'),
                hasProduct: !!document.querySelector('[class*="product"]'),
                htmlSnippet: document.body?.innerHTML?.substring(0, 1000)
            }
        }""")

        print(f"\nPage Analysis:")
        print(f"  Product cards found: {page_text['productCards']}")
        print(f"  Total divs: {page_text['allDivs']}")
        print(f"  Has price elements: {page_text['hasPrice']}")
        print(f"  Has product elements: {page_text['hasProduct']}")

        print(f"\nBody text preview:")
        print(page_text['bodyText'][:300])

        print(f"\nHTML snippet:")
        print(page_text['htmlSnippet'][:500])

        # Look for any product-like elements
        print(f"\nSearching for product containers...")
        product_info = await page.evaluate("""() => {
            const results = [];

            // Check common selectors
            const selectors = [
                '[data-testid="product-item"]',
                '.product-card',
                '[class*="ProductCard"]',
                '[class*="product-card"]',
                'article',
                '[role="article"]'
            ];

            selectors.forEach(sel => {
                const els = document.querySelectorAll(sel);
                if (els.length > 0) {
                    const sample = els[0];
                    results.push({
                        selector: sel,
                        count: els.length,
                        className: sample.className,
                        innerHTML: sample.innerHTML?.substring(0, 200)
                    });
                }
            });

            return results;
        }""")

        for info in product_info:
            print(f"\n  Selector: {info['selector']}")
            print(f"  Count: {info['count']}")
            print(f"  Class: {info['className'][:100]}")
            print(f"  HTML: {info['innerHTML'][:200]}")

        await browser.close()


async def main():
    """Diagnose a few search queries."""
    queries = ["milk", "bananas", "bread"]

    for query in queries:
        print("\n" + "=" * 80)
        print(f"DIAGNOSING: {query}")
        print("=" * 80)
        await diagnose_search_page(query)
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
