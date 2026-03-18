#!/usr/bin/env python3
"""Inspect Coles search page DOM structure."""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def inspect_dom_structure() -> None:
    """Inspect the actual DOM structure of Coles search page."""
    print("=" * 60)
    print("Coles DOM Structure Inspector")
    print("=" * 60)
    print()

    async with async_playwright() as p:
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to Coles search page
        url = "https://www.coles.com.au/search?q=milk"
        print(f"📄 Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print("   ✓ Page loaded")

        # Wait for products to load
        print("⏳ Waiting for products to load (10 seconds)...")
        await asyncio.sleep(10)

        # Inspect DOM structure
        print("\n🔍 Inspecting DOM structure...")

        dom_info = await page.evaluate("""() => {
            const info = {
                title: document.title,
                url: window.location.href,
                bodyClasses: document.body.className,
                productCandidates: []
            };

            // Look for any elements that might contain products
            const candidateSelectors = [
                '[data-testid*="product" i]',
                '[class*="product" i]',
                '[class*="Product" i]',
                '[class*="item" i]',
                '[class*="Item" i]',
                'article',
                '[role="article"]',
            ];

            candidateSelectors.forEach(selector => {
                try {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        const sample = elements[0];
                        const html = sample.outerHTML.substring(0, 200);
                        info.productCandidates.push({
                            selector: selector,
                            count: elements.length,
                            sample: html
                        });
                    }
                } catch(e) {
                    // Ignore selector errors
                }
            });

            // Look for any text content that might indicate products
            const allText = document.body.innerText;
            const milkCount = (allText.match(/milk/gi) || []).length;
            info.milkMentions = milkCount;

            // Look for price patterns
            const pricePattern = /\$[0-9]+\.[0-9]{2}/g;
            const prices = allText.match(pricePattern) || [];
            info.priceCount = prices.length;
            info.samplePrices = prices.slice(0, 5);

            return info;
        }""")

        print(f"\n   Page Title: {dom_info['title']}")
        print(f"   URL: {dom_info['url']}")
        print(f"   Body Classes: {dom_info['bodyClasses']}")
        print(f"   'milk' mentions in page: {dom_info['milkMentions']}")
        print(f"   Price patterns found: {dom_info['priceCount']}")

        if dom_info['samplePrices']:
            print(f"   Sample prices: {dom_info['samplePrices']}")

        print(f"\n   Product candidate elements:")
        for candidate in dom_info['productCandidates'][:10]:
            print(f"   - {candidate['selector']}: {candidate['count']} elements")
            print(f"     Sample: {candidate['sample'][:100]}...")

        # Get full HTML of body for analysis
        print(f"\n💾 Saving full page HTML to /tmp/coles_search_page.html")
        html_content = await page.content()
        with open("/tmp/coles_search_page.html", "w") as f:
            f.write(html_content)

        # Also save DOM info
        print(f"💾 Saving DOM info to /tmp/coles_dom_info.json")
        with open("/tmp/coles_dom_info.json", "w") as f:
            json.dump(dom_info, f, indent=2)

        print("\n⏸️ Pausing for 10 seconds - check browser visually...")
        print("   Look at the page structure and see if products are visible")
        await asyncio.sleep(10)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(inspect_dom_structure())