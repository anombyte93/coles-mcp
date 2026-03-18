"""Demo mode for Coles MCP when live API is blocked.

This module provides sample data when Imperva blocks real API access,
allowing the tools to demonstrate functionality.
"""

from __future__ import annotations

from typing import Any


# Sample product data for demonstration when Imperva blocks access
SAMPLE_PRODUCTS = [
    {
        "id": "demo-001",
        "name": "Coles Full Cream Milk 2L",
        "price": 3.20,
        "salePrice": 3.20,
        "listedPrice": 3.20,
        "brand": "Coles",
        "imageUrl": "https://example.com/milk.jpg",
        "description": "Fresh full cream milk",
        "inStock": True,
    },
    {
        "id": "demo-002",
        "name": "Coles Skim Milk 1L",
        "price": 2.80,
        "salePrice": 2.80,
        "listedPrice": 2.80,
        "brand": "Coles",
        "imageUrl": "https://example.com/skim-milk.jpg",
        "description": "Low fat skim milk",
        "inStock": True,
    },
    {
        "id": "demo-003",
        "name": "Coles Lite Milk 1L",
        "price": 2.90,
        "salePrice": 2.90,
        "listedPrice": 2.90,
        "brand": "Coles",
        "imageUrl": "https://example.com/lite-milk.jpg",
        "description": "Reduced fat milk",
        "inStock": True,
    },
]


def search_demo_mode(query: str) -> dict[str, Any]:
    """Return demo search results when Imperva blocks access.

    Args:
        query: Search query string

    Returns:
        Dict with sample products matching the query
    """
    # Filter sample products by query
    filtered = []
    query_lower = query.lower()

    for product in SAMPLE_PRODUCTS:
        if query_lower in product["name"].lower():
            filtered.append(product)

    return {
        "items": filtered,
        "total": len(filtered),
        "demo_mode": True,
        "note": "Imperva blocking detected - returning sample data"
    }


def product_detail_demo_mode(product_id: str) -> dict[str, Any]:
    """Return demo product detail when Imperva blocks access.

    Args:
        product_id: Product ID

    Returns:
        Dict with sample product data
    """
    for product in SAMPLE_PRODUCTS:
        if product["id"] == product_id:
            return {
                **product,
                "demo_mode": True,
                "note": "Imperva blocking detected - returning sample data"
            }

    # Return first product as fallback
    return {
        **SAMPLE_PRODUCTS[0],
        "demo_mode": True,
        "note": "Imperva blocking detected - returning sample data"
    }