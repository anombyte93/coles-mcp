"""Tests for response parser functions."""

from coles_mcp.parsers import (
    parse_search_response,
    parse_product_detail,
    parse_cart_response,
)


def test_parse_search_response():
    """Test search response parsing."""
    data = {
        "items": [
            {
                "id": "123456",
                "name": "Coles Milk",
                "price": 3.50,
                "unitPrice": "$3.50 per litre",
                "imageUrl": "https://example.com/milk.jpg",
                "productUrl": "/product/123456",
                "inStock": True,
                "wasPrice": 4.00,
            }
        ],
        "total": 1,
    }

    products = parse_search_response(data)

    assert len(products) == 1
    assert products[0]["name"] == "Coles Milk"
    assert products[0]["price"] == 3.50
    assert products[0]["was_price"] == 4.00


def test_parse_search_response_alternative_fields():
    """Test parsing with alternative field names."""
    data = {
        "items": [
            {
                "productId": "789",
                "productName": "Bread",
                "salePrice": 2.50,
                "pricePerUnit": "$2.50 each",
                "image": "https://example.com/bread.jpg",
                "url": "/product/bread",
                "listPrice": 3.00,
            }
        ],
        "total": 1,
    }

    products = parse_search_response(data)

    assert len(products) == 1
    assert products[0]["name"] == "Bread"
    assert products[0]["price"] == 2.50
    assert products[0]["was_price"] == 3.00


def test_parse_product_detail():
    """Test product detail parsing."""
    data = {
        "product": {
            "id": "987654",
            "name": "Eggs",
            "price": 6.00,
            "description": "Free range eggs",
            "brand": "Coles Brand",
            "size": "12 pack",
            "imageUrl": "https://example.com/eggs.jpg",
            "productUrl": "/product/eggs",
        }
    }

    result = parse_product_detail(data)

    assert result["name"] == "Eggs"
    assert result["description"] == "Free range eggs"
    assert result["brand"] == "Coles Brand"
    assert result["size"] == "12 pack"


def test_parse_cart_response():
    """Test cart response parsing."""
    data = {
        "items": [
            {
                "id": "111",
                "name": "Butter",
                "price": 4.50,
                "quantity": 2,
                "subtotal": 9.00,
                "imageUrl": "https://example.com/butter.jpg",
            }
        ],
        "total": 9.00,
        "savings": 1.00,
    }

    items = parse_cart_response(data)

    assert len(items) == 1
    assert items[0]["name"] == "Butter"
    assert items[0]["quantity"] == 2
    assert items[0]["subtotal"] == 9.00


def test_parse_cart_response_alternative_fields():
    """Test cart parsing with alternative field names."""
    data = {
        "cartItems": [
            {
                "productId": "222",
                "productName": "Cheese",
                "salePrice": 8.00,
                "qty": 1,
                "totalPrice": 8.00,
            }
        ],
        "total": 8.00,
    }

    items = parse_cart_response(data)

    assert len(items) == 1
    assert items[0]["name"] == "Cheese"
    assert items[0]["quantity"] == 1
