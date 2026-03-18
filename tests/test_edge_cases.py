"""Edge case tests for Coles MCP server.

Tests various edge cases and error scenarios to ensure robustness.
"""

import pytest
from coles_mcp.demo_mode import (
    search_demo_mode,
    product_detail_demo_mode,
    specials_demo_mode,
    view_cart_demo_mode,
    add_to_cart_demo_mode,
)


class TestDemoModeEdgeCases:
    """Test edge cases in demo mode functions."""

    def test_search_empty_query(self):
        """Test search with empty query."""
        result = search_demo_mode("")
        assert result["demo_mode"] == True
        # Empty query should return all products or empty
        assert isinstance(result["total"], int)

    def test_search_case_insensitive(self):
        """Test that search is case-insensitive."""
        result1 = search_demo_mode("MILK")
        result2 = search_demo_mode("milk")
        result3 = search_demo_mode("MiLk")
        # All should return same results
        assert result1["total"] == result2["total"] == result3["total"]

    def test_search_no_results(self):
        """Test search with query that has no matches."""
        result = search_demo_mode("xyznonexistentproduct123")
        assert result["demo_mode"] == True
        assert result["total"] == 0
        assert len(result["items"]) == 0

    def test_product_detail_unknown_id(self):
        """Test product detail with unknown ID returns fallback."""
        result = product_detail_demo_mode("unknown-xyz-999")
        assert result["demo_mode"] == True
        # Should return first product as fallback
        assert result["name"] == "Coles Full Cream Milk 2L"

    def test_specials_with_category(self):
        """Test specials with category filter."""
        result = specials_demo_mode(category_id="dairy", page_num=1)
        assert result["demo_mode"] == True
        assert result["total"] > 0
        assert result["page"] == 1

    def test_specials_pagination(self):
        """Test specials pagination."""
        result1 = specials_demo_mode(page_num=1)
        result2 = specials_demo_mode(page_num=2)
        assert result1["demo_mode"] == True
        assert result2["demo_mode"] == True
        # Both should return data (demo mode doesn't paginate)
        assert result1["total"] > 0

    def test_add_to_cart_quantity(self):
        """Test add to cart with different quantities."""
        result1 = add_to_cart_demo_mode("demo-001", quantity=1)
        result2 = add_to_cart_demo_mode("demo-001", quantity=5)
        assert result1["demo_mode"] == True
        assert result2["demo_mode"] == True
        # Check quantities
        assert result1["items"][0]["quantity"] == 1
        assert result2["items"][0]["quantity"] == 5
        # Check totals
        assert result1["total"] < result2["total"]

    def test_add_to_cart_zero_quantity(self):
        """Test add to cart with zero quantity."""
        result = add_to_cart_demo_mode("demo-001", quantity=0)
        assert result["demo_mode"] == True
        # Should still return a valid cart structure

    def test_view_cart_structure(self):
        """Test view cart returns proper structure."""
        result = view_cart_demo_mode()
        assert result["demo_mode"] == True
        assert "items" in result
        assert "total" in result
        assert "item_count" in result
        assert isinstance(result["items"], list)
        assert isinstance(result["total"], (int, float))
        assert isinstance(result["item_count"], int)

    def test_demo_mode_flag_always_set(self):
        """Test that demo_mode flag is always set."""
        functions = [
            search_demo_mode,
            product_detail_demo_mode,
            specials_demo_mode,
            view_cart_demo_mode,
            add_to_cart_demo_mode,
        ]

        for func in functions:
            if func.__name__ == "specials_demo_mode":
                result = func()
            elif func.__name__ == "add_to_cart_demo_mode":
                result = func("demo-001")
            elif func.__name__ == "view_cart_demo_mode":
                result = func()
            elif func.__name__ == "search_demo_mode":
                result = func("test")
            else:
                result = func("demo-001")

            assert result.get("demo_mode") == True, f"{func.__name__} should have demo_mode=True"

    def test_product_data_completeness(self):
        """Test that sample products have all required fields."""
        required_fields = [
            "id", "name", "price", "salePrice", "listedPrice",
            "brand", "imageUrl", "description", "inStock"
        ]

        from coles_mcp.demo_mode import SAMPLE_PRODUCTS

        for product in SAMPLE_PRODUCTS:
            for field in required_fields:
                assert field in product, f"Product {product.get('id')} missing field: {field}"

    def test_search_returns_valid_prices(self):
        """Test that search returns valid price data."""
        result = search_demo_mode("milk")
        for product in result["items"]:
            price = product.get("price", 0)
            sale_price = product.get("salePrice", 0)
            listed_price = product.get("listedPrice", 0)
            # Prices should be numeric
            assert isinstance(price, (int, float))
            assert isinstance(sale_price, (int, float))
            assert isinstance(listed_price, (int, float))
            # Prices should be positive
            assert price >= 0
            assert sale_price >= 0
            assert listed_price >= 0

    def test_specials_include_discount_info(self):
        """Test that specials include discount information."""
        result = specials_demo_mode()
        for item in result["items"]:
            # If sale price < listed price, should have discount
            if item["salePrice"] < item["listedPrice"]:
                assert "discount" in item
                assert isinstance(item["discount"], (int, float))
                assert 0 <= item["discount"] <= 100
