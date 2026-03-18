"""Demo mode for Coles MCP when live API is blocked.

This module provides sample data when Imperva blocks real API access,
allowing the tools to demonstrate functionality.
"""

from __future__ import annotations

from typing import Any


# Sample product data for demonstration when Imperva blocks access
SAMPLE_PRODUCTS = [
    # Dairy
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
    {
        "id": "demo-004",
        "name": "Coles Butter Salted 250g",
        "price": 4.50,
        "salePrice": 4.50,
        "listedPrice": 4.50,
        "brand": "Coles",
        "imageUrl": "https://example.com/butter.jpg",
        "description": "Salted butter block",
        "inStock": True,
    },
    {
        "id": "demo-005",
        "name": "Coles Free Range Eggs 12 Pack",
        "price": 6.80,
        "salePrice": 5.50,
        "listedPrice": 6.80,
        "brand": "Coles",
        "imageUrl": "https://example.com/eggs.jpg",
        "description": "Free range large eggs",
        "inStock": True,
    },
    # Bakery
    {
        "id": "demo-006",
        "name": "Coles White Sandwich Bread 700g",
        "price": 3.00,
        "salePrice": 3.00,
        "listedPrice": 3.00,
        "brand": "Coles",
        "imageUrl": "https://example.com/bread.jpg",
        "description": "Soft white sandwich bread",
        "inStock": True,
    },
    {
        "id": "demo-007",
        "name": "Coles Wholemeal Bread 700g",
        "price": 3.50,
        "salePrice": 3.50,
        "listedPrice": 3.50,
        "brand": "Coles",
        "imageUrl": "https://example.com/wholemeal.jpg",
        "description": "Healthy wholemeal bread",
        "inStock": True,
    },
    # Meat
    {
        "id": "demo-008",
        "name": "Coles Rump Steak 500g",
        "price": 12.00,
        "salePrice": 10.00,
        "listedPrice": 12.00,
        "brand": "Coles",
        "imageUrl": "https://example.com/steak.jpg",
        "description": "Premium grass-fed beef",
        "inStock": True,
    },
    {
        "id": "demo-009",
        "name": "Coles Chicken Breast 600g",
        "price": 14.00,
        "salePrice": 14.00,
        "listedPrice": 14.00,
        "brand": "Coles",
        "imageUrl": "https://example.com/chicken.jpg",
        "description": "Boneless skinless chicken breast",
        "inStock": True,
    },
    # Produce
    {
        "id": "demo-010",
        "name": "Coles Bananas 1kg",
        "price": 3.50,
        "salePrice": 3.50,
        "listedPrice": 3.50,
        "brand": "Coles",
        "imageUrl": "https://example.com/bananas.jpg",
        "description": "Fresh cavendish bananas",
        "inStock": True,
    },
    {
        "id": "demo-011",
        "name": "Coles Apples Royal Gala 1kg",
        "price": 5.00,
        "salePrice": 4.00,
        "listedPrice": 5.00,
        "brand": "Coles",
        "imageUrl": "https://example.com/apples.jpg",
        "description": "Sweet royal gala apples",
        "inStock": True,
    },
    {
        "id": "demo-012",
        "name": "Coles Carrots 1kg Bag",
        "price": 2.50,
        "salePrice": 2.50,
        "listedPrice": 2.50,
        "brand": "Coles",
        "imageUrl": "https://example.com/carrots.jpg",
        "description": "Fresh Australian carrots",
        "inStock": True,
    },
    # Pantry
    {
        "id": "demo-013",
        "name": "Coles Tomato Ketchup 500ml",
        "price": 2.80,
        "salePrice": 2.80,
        "listedPrice": 2.80,
        "brand": "Coles",
        "imageUrl": "https://example.com/ketchup.jpg",
        "description": "Classic tomato ketchup",
        "inStock": True,
    },
    {
        "id": "demo-014",
        "name": "Coles Pasta Penne 500g",
        "price": 1.50,
        "salePrice": 1.50,
        "listedPrice": 1.50,
        "brand": "Coles",
        "imageUrl": "https://example.com/pasta.jpg",
        "description": "Italian-style penne pasta",
        "inStock": True,
    },
    {
        "id": "demo-015",
        "name": "Coles Coffee Beans Instant 100g",
        "price": 4.20,
        "salePrice": 4.20,
        "listedPrice": 4.20,
        "brand": "Coles",
        "imageUrl": "https://example.com/coffee.jpg",
        "description": "Premium instant coffee",
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


def specials_demo_mode(category_id: str = "", page_num: int = 1) -> dict[str, Any]:
    """Return demo specials when Imperva blocks access.

    Args:
        category_id: Optional category filter
        page_num: Page number for pagination

    Returns:
        Dict with sample special offers
    """
    # Return first 5 products as "specials"
    special_items = SAMPLE_PRODUCTS[:5]

    # Add discount info for demo
    for item in special_items:
        if item["salePrice"] < item["listedPrice"]:
            item["discount"] = round((1 - item["salePrice"] / item["listedPrice"]) * 100, 1)
            item["special_text"] = f"Save ${item['listedPrice'] - item['salePrice']:.2f}"

    return {
        "items": special_items,
        "total": len(special_items),
        "page": page_num,
        "demo_mode": True,
        "note": "Imperva blocking detected - returning sample specials"
    }


def view_cart_demo_mode() -> dict[str, Any]:
    """Return demo cart contents when Imperva blocks access.

    Returns:
        Dict with sample cart data
    """
    cart_items = [
        {
            **SAMPLE_PRODUCTS[0],
            "quantity": 2,
            "subtotal": SAMPLE_PRODUCTS[0]["price"] * 2,
        },
        {
            **SAMPLE_PRODUCTS[4],
            "quantity": 1,
            "subtotal": SAMPLE_PRODUCTS[4]["price"],
        },
    ]

    total = sum(item["subtotal"] for item in cart_items)

    return {
        "items": cart_items,
        "total": total,
        "item_count": len(cart_items),
        "demo_mode": True,
        "note": "Imperva blocking detected - returning sample cart"
    }


def add_to_cart_demo_mode(product_id: str, quantity: int = 1) -> dict[str, Any]:
    """Return demo add to cart response when Imperva blocks access.

    Args:
        product_id: Product ID to add
        quantity: Quantity to add

    Returns:
        Dict with sample cart response
    """
    # Find product or use first
    product = next((p for p in SAMPLE_PRODUCTS if p["id"] == product_id), SAMPLE_PRODUCTS[0])

    return {
        "items": [
            {
                **product,
                "quantity": quantity,
                "subtotal": product["price"] * quantity,
            }
        ],
        "total": product["price"] * quantity,
        "item_count": 1,
        "demo_mode": True,
        "note": "Imperva blocking detected - returning sample add to cart response"
    }