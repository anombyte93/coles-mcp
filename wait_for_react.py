#!/usr/bin/env python3
"""Wait for React rendering and extract prices."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from playwright.async_api import async_playwright
from coles_mcp.config import load_config


async def search_with_react_wait(query: str) -> dict | None:
    """Search Coles with proper React rendering wait."""

    config = load_config()
    browser_url = config.browser.cdp_url

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(browser_url)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        search_url = f"https://www.coles.com.au/search?q={query}"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        # Wait for React to finish rendering
        print(f"  Waiting for React rendering...", end=" ")
        await page.wait_for_timeout(8000)  # Give React time to render

        # Wait for network to be idle
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass

        print("done")

        # Now extract ALL text content and look for products
        content = await page.evaluate("""() => {
            // Get all text from the page
            const bodyText = document.body?.textContent || '';

            // Look for price patterns
            const pricePattern = /\$(\d+)\.(\d{2})/g;
            const prices = [];
            let match;
            while ((match = pricePattern.exec(bodyText)) !== null) {
                prices.push(`${match[1]}.${match[2]}`);
            }

            // Try to find product names and their prices
            // This is a heuristic approach since we don't know the exact DOM structure
            const results = [];

            // Look for elements that might be products
            const allElements = document.querySelectorAll('*');
            const potentialProducts = [];

            allElements.forEach(el => {
                const text = el.textContent?.trim() || '';
                const hasPrice = text.includes('$') && text.match(/\$\d+\.\d{2}/);

                if (hasPrice && text.length < 200 && text.length > 10) {
                    // This might be a product element
                    potentialProducts.push({
                        tag: el.tagName,
                        class: el.className,
                        text: text.substring(0, 100)
                    });
                }
            });

            return {
                url: window.location.href,
                prices: prices.slice(0, 20),  // First 20 prices found
                potentialProductCount: potentialProducts.length,
                bodySample: bodyText.substring(0, 1000),
                potentialProducts: potentialProducts.slice(0, 5)  // First 5 candidates
            };
        }""")

        print(f"  URL: {content['url']}")
        print(f"  Prices found: {len(content['prices'])}")
        print(f"  Potential products: {content['potentialProductCount']}")

        if content['prices']:
            print(f"  Sample prices: {content['prices'][:5]}")

        if content['potentialProducts']:
            print(f"  Sample product elements:")
            for i, prod in enumerate(content['potentialProducts'][:3]):
                print(f"    {i+1}. {prod['text'][:60]}")

        # Take a screenshot to see what's actually rendered
        screenshot_path = f"/tmp/coles_search_{query.replace(' ', '_')}.png"
        await page.screenshot(path=screenshot_path, full_page=False)
        print(f"  Screenshot saved to: {screenshot_path}")

        await browser.close()

        return content


async def main():
    """Test search with React rendering wait."""

    queries = ["milk", "bananas"]

    for query in queries:
        print(f"\n{'='*80}")
        print(f"SEARCH: {query}")
        print('='*80)
        await search_with_react_wait(query)


if __name__ == "__main__":
    asyncio.run(main())
