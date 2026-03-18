"""DOM parsing fallback for Coles when API is blocked by Incapsula.

This module provides parsing functions to extract product information
from Coles website HTML when API calls are blocked.
"""

from __future__ import annotations

from typing import Any

from playwright.async_api import Page


async def parse_search_results(page: Page) -> dict[str, Any]:
    """Parse product search results from Coles search page DOM.

    This is a fallback function when API calls are blocked by Incapsula.
    It navigates to the search URL and parses product information from the HTML.

    Args:
        page: Playwright page object (must be on Coles website)

    Returns:
        Dict with 'items' list and 'total' count, mimicking API response structure
    """
    # Extract product data from DOM
    products = await page.evaluate("""() => {
        // Look for product cards in the DOM
        // Coles uses various selectors depending on page layout
        const selectors = [
            '[data-testid="product-item"]',
            '.product-item',
            '[class*="product"]',
            '[class*="ProductCard"]',
        ];

        let items = [];

        for (const selector of selectors) {
            const elements = document.querySelectorAll(selector);
            if (elements.length > 0) {
                elements.forEach(el => {
                    // Try to extract product data
                    const name = el.querySelector('[class*="name"], [class*="title"], h3, h4')?.textContent?.trim() || '';
                    const priceText = el.querySelector('[class*="price"], [class*="Price"]')?.textContent?.trim() || '';
                    const price = parseFloat(priceText.replace(/[^0-9.]/g, '')) || 0;
                    const link = el.querySelector('a')?.href || '';
                    const image = el.querySelector('img')?.src || '';

                    if (name) {
                        items.push({
                            name: name,
                            price: price,
                            salePrice: price,
                            listedPrice: price,
                            url: link,
                            image: image,
                        });
                    }
                });
                break;  // Use first successful selector
            }
        }

        return {
            items: items,
            total: items.length
        };
    }""")

    return products


async def search_via_dom(page: Page, query: str, store_id: str = "0357") -> dict[str, Any]:
    """Perform search by navigating to search results page and parsing DOM.

    Args:
        page: Playwright page object
        query: Search query string
        store_id: Coles store ID for context

    Returns:
        Dict with 'items' list and 'total' count
    """
    # Navigate to search results page
    search_url = f"https://www.coles.com.au/search?q={query}"
    await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

    # Wait for page to load and render products
    await page.wait_for_timeout(3000)

    # Parse products from DOM
    result = await parse_search_results(page)

    return result