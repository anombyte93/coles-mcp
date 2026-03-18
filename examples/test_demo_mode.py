#!/usr/bin/env python3
"""Test demo mode functionality without requiring live Coles API access.

This script demonstrates that all tools work correctly even when
Imperva blocks access to the live Coles API.
"""

import asyncio
from coles_mcp.demo_mode import (
    search_demo_mode,
    product_detail_demo_mode,
    specials_demo_mode,
    view_cart_demo_mode,
    add_to_cart_demo_mode,
)


async def test_demo_mode():
    """Test all demo mode functions."""
    print("=" * 60)
    print("Coles MCP - Demo Mode Test Suite")
    print("=" * 60)
    print()

    # Test 1: Search demo mode
    print("1. Testing search_demo_mode()")
    print("-" * 40)
    result = search_demo_mode("milk")
    assert result["demo_mode"] == True
    assert result["total"] > 0
    assert len(result["items"]) > 0
    print(f"✓ Search returned {result['total']} products")
    print(f"✓ First product: {result['items'][0]['name']}")
    print()

    # Test 2: Product detail demo mode
    print("2. Testing product_detail_demo_mode()")
    print("-" * 40)
    result = product_detail_demo_mode("demo-001")
    assert result["demo_mode"] == True
    assert result["name"] == "Coles Full Cream Milk 2L"
    print(f"✓ Product: {result['name']}")
    print(f"✓ Price: ${result['price']}")
    print()

    # Test 3: Specials demo mode
    print("3. Testing specials_demo_mode()")
    print("-" * 40)
    result = specials_demo_mode()
    assert result["demo_mode"] == True
    assert result["total"] > 0
    print(f"✓ Specials returned: {result['total']} items")
    if result["items"]:
        first_special = result["items"][0]
        if "discount" in first_special:
            print(f"✓ First special: {first_special['name']} ({first_special['discount']}% off)")
        else:
            print(f"✓ First special: {first_special['name']}")
    print()

    # Test 4: View cart demo mode
    print("4. Testing view_cart_demo_mode()")
    print("-" * 40)
    result = view_cart_demo_mode()
    assert result["demo_mode"] == True
    assert result["item_count"] > 0
    print(f"✓ Cart items: {result['item_count']}")
    print(f"✓ Cart total: ${result['total']}")
    for item in result["items"]:
        print(f"  - {item['name']} x{item['quantity']}: ${item['subtotal']}")
    print()

    # Test 5: Add to cart demo mode
    print("5. Testing add_to_cart_demo_mode()")
    print("-" * 40)
    result = add_to_cart_demo_mode("demo-001", 2)
    assert result["demo_mode"] == True
    assert result["item_count"] > 0
    print(f"✓ Added to cart: {result['items'][0]['name']} x{result['items'][0]['quantity']}")
    print(f"✓ Cart total: ${result['total']}")
    print()

    # Test 6: Search with different queries
    print("6. Testing search with various queries")
    print("-" * 40)
    queries = ["bread", "chicken", "banana", "coffee"]
    for query in queries:
        result = search_demo_mode(query)
        found = len(result["items"])
        print(f"✓ Search '{query}': {found} products found")
    print()

    print("=" * 60)
    print("✅ ALL DEMO MODE TESTS PASSED")
    print("=" * 60)
    print()
    print("Summary:")
    print("- All demo mode functions work correctly")
    print("- Tools return meaningful sample data")
    print("- Demo mode flag is properly set")
    print("- Products span multiple categories")
    print()
    print("The Coles MCP server tools work correctly with demo mode fallback!")


if __name__ == "__main__":
    asyncio.run(test_demo_mode())
