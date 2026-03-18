"""Edge case tests for response parser functions."""

from coles_mcp.parsers import (
    parse_search_response,
    parse_product_detail,
    parse_cart_response,
)


def test_parse_search_response_empty_items():
    """Test parsing with empty items list."""
    data = {"items": [], "total": 0}
    products = parse_search_response(data)

    assert len(products) == 0


def test_parse_search_response_missing_fields():
    """Test parsing with all optional fields missing."""
    data = {
        "items": [
            {
                "id": "123",
                # All other fields missing
            }
        ],
        "total": 1,
    }

    products = parse_search_response(data)

    assert len(products) == 1
    assert products[0]["product_id"] == "123"
    assert products[0]["name"] == ""
    assert products[0]["price"] == 0
    assert products[0]["in_stock"] is True  # Default


def test_parse_search_response_null_values():
    """Test parsing with explicit null values."""
    data = {
        "items": [
            {
                "id": "456",
                "name": None,
                "price": None,
                "imageUrl": None,
                "inStock": None,
            }
        ],
        "total": 1,
    }

    products = parse_search_response(data)

    assert len(products) == 1
    assert products[0]["name"] == ""
    assert products[0]["price"] == 0
    assert products[0]["image_url"] is None
    assert products[0]["in_stock"] is True  # None treated as True


def test_parse_search_response_no_items_key():
    """Test parsing when 'items' key is missing."""
    data = {"total": 0}
    products = parse_search_response(data)

    assert len(products) == 0


def test_parse_product_detail_missing_product_key():
    """Test parsing when 'product' key is missing."""
    data = {"id": "789", "name": "Test", "price": 1.99}
    result = parse_product_detail(data)

    # Falls back to root dict
    assert result["product_id"] == "789"
    assert result["name"] == "Test"
    assert result["price"] == 1.99


def test_parse_product_detail_empty_dict():
    """Test parsing with empty product dict."""
    data = {"product": {}}
    result = parse_product_detail(data)

    assert result["name"] == ""
    assert result["price"] == 0
    assert result["product_id"] == ""


def test_parse_cart_response_empty_items():
    """Test parsing cart with empty items."""
    data = {"items": [], "total": 0}
    items = parse_cart_response(data)

    assert len(items) == 0


def test_parse_cart_response_missing_quantity():
    """Test parsing when quantity field is missing."""
    data = {
        "items": [
            {
                "id": "999",
                "name": "Test Item",
                "price": 5.00,
                # quantity missing
            }
        ],
        "total": 5.00,
    }

    items = parse_cart_response(data)

    assert len(items) == 1
    assert items[0]["quantity"] == 0
    assert items[0]["subtotal"] == 0  # price * 0


def test_parse_cart_response_cartitems_key():
    """Test parsing with 'cartItems' key instead of 'items'."""
    data = {
        "cartItems": [
            {
                "productId": "888",
                "productName": "Cart Item",
                "salePrice": 3.50,
                "qty": 2,
            }
        ],
        "total": 7.00,
    }

    items = parse_cart_response(data)

    assert len(items) == 1
    assert items[0]["product_id"] == "888"
    assert items[0]["name"] == "Cart Item"
    assert items[0]["quantity"] == 2
    assert items[0]["subtotal"] == 7.00


def test_parse_cart_response_zero_quantity():
    """Test parsing with zero quantity."""
    data = {
        "items": [
            {
                "id": "777",
                "name": "Zero Item",
                "price": 10.00,
                "quantity": 0,
            }
        ],
        "total": 0,
    }

    items = parse_cart_response(data)

    assert len(items) == 1
    assert items[0]["quantity"] == 0
    assert items[0]["subtotal"] == 0
