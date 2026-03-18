"""Browser automation fallback tools for Coles when API is blocked.

This module implements tools using Playwright browser automation
to interact with Coles website when API calls are blocked by Imperva.
"""

from __future__ import annotations

from typing import Any

from playwright.async_api import Page


async def search_products_via_browser(
    page: Page, query: str, store_id: str = "0357"
) -> dict[str, Any]:
    """Search products using browser automation (API fallback).

    Navigates to Coles search page and extracts product information
    from the rendered DOM.

    Args:
        page: Playwright page object
        query: Search query
        store_id: Coles store ID for context

    Returns:
        Dict with 'items' list and 'total' count
    """
    # Navigate to search page
    search_url = f"https://www.coles.com.au/search?q={query}"
    await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

    # Wait for page to load and render
    await page.wait_for_timeout(5000)

    # Try to extract product data from the page
    products = await page.evaluate("""() => {
        // Look for product information in the page
        const items = [];

        // Try different selector patterns that Coles might use
        const selectors = [
            '[data-testid*="product"]',
            '[class*="product-item"]',
            '[class*="ProductCard"]',
            'article[class*="product"]',
        ];

        for (const selector of selectors) {
            const elements = document.querySelectorAll(selector);
            if (elements.length > 0) {
                elements.forEach(el => {
                    const nameEl = el.querySelector('[class*="name"], [class*="title"], h3, h4');
                    const priceEl = el.querySelector('[class*="price"], [class*="Price"]');
                    const linkEl = el.querySelector('a');

                    const name = nameEl?.textContent?.trim() || '';
                    const priceText = priceEl?.textContent?.trim() || '';
                    const price = parseFloat(priceText.replace(/[^0-9.]/g, '')) || 0;
                    const url = linkEl?.href || '';

                    if (name) {
                        items.push({
                            name: name,
                            price: price,
                            salePrice: price,
                            url: url
                        });
                    }
                });

                if (items.length > 0) {
                    break;  // Found products with this selector
                }
            }
        }

        return {
            items: items,
            total: items.length
        };
    }""")

    return products