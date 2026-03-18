"""Tests for MCP server tools."""

import pytest


@pytest.mark.asyncio
async def test_server_has_all_tools():
    """Test that all 11 MCP tools are registered."""
    from coles_mcp import server

    # FastMCP stores tools differently - check the mcp instance
    # We can verify by checking that the tool functions exist
    expected_tools = [
        "coles_health_check",
        "coles_login",
        "coles_login_with_credentials",
        "coles_search",
        "coles_product_detail",
        "coles_specials",
        "coles_bulk_products",
        "coles_add_to_cart",
        "coles_view_cart",
        "coles_delivery_setup",
        "coles_select_time_slot",
    ]

    # Verify each tool function exists in the server module
    for tool_name in expected_tools:
        assert hasattr(server, tool_name), f"Missing tool: {tool_name}"

    # Verify they are callable
    for tool_name in expected_tools:
        tool_func = getattr(server, tool_name)
        assert callable(tool_func), f"Tool {tool_name} is not callable"


@pytest.mark.asyncio
async def test_models_import():
    """Test that all models can be imported."""
    from coles_mcp.models import Product, ProductDetail, CartItem, Cart

    # Test basic model creation
    product = Product(
        name="Test",
        price=1.99,
        product_id="123",
        product_url="/test",
    )
    assert product.name == "Test"

    product_detail = ProductDetail(
        name="Test Detail",
        price=2.99,
        product_id="456",
        product_url="/test-detail",
    )
    assert product_detail.name == "Test Detail"

    cart_item = CartItem(
        name="Test Item",
        quantity=2,
        price=1.50,
        subtotal=3.00,
        product_id="789",
    )
    assert cart_item.quantity == 2

    cart = Cart(items=[], total=0)
    assert cart.total == 0


@pytest.mark.asyncio
async def test_config_loads():
    """Test that config can be loaded."""
    from coles_mcp.config import load_config

    config = load_config()
    assert config.site == "coles.com.au"
    assert config.browser.cdp_port is not None
    assert config.store.store_id is not None


@pytest.mark.asyncio
async def test_api_class_structure():
    """Test ColesAPI class structure."""
    from coles_mcp.api import ColesAPI
    from unittest.mock import AsyncMock

    mock_page = AsyncMock()
    api = ColesAPI(mock_page, "")

    # Test methods exist
    assert hasattr(api, "check_auth")
    assert hasattr(api, "search")
    assert hasattr(api, "product_detail")
    assert hasattr(api, "specials")
    assert hasattr(api, "add_to_cart")
    assert hasattr(api, "view_cart")
    assert hasattr(api, "bulk_products")
    assert hasattr(api, "delivery_setup")
    assert hasattr(api, "health_check")
    assert hasattr(api, "_discover_subscription_key")
    assert hasattr(api, "_get_subscription_key")


@pytest.mark.asyncio
async def test_parser_functions():
    """Test parser functions exist and work."""
    from coles_mcp.parsers import (
        parse_search_response,
        parse_product_detail,
        parse_cart_response,
    )

    # Test parse_search_response
    search_data = {
        "items": [
            {
                "id": "123",
                "name": "Test Product",
                "price": 5.99,
            }
        ],
        "total": 1,
    }
    products = parse_search_response(search_data)
    assert len(products) == 1
    assert products[0]["name"] == "Test Product"

    # Test parse_product_detail
    detail_data = {
        "product": {
            "id": "456",
            "name": "Detail Product",
            "price": 3.99,
        }
    }
    detail = parse_product_detail(detail_data)
    assert detail["name"] == "Detail Product"

    # Test parse_cart_response
    cart_data = {
        "items": [
            {
                "id": "789",
                "name": "Cart Item",
                "price": 2.50,
                "quantity": 3,
                "subtotal": 7.50,
            }
        ],
        "total": 7.50,
    }
    cart_items = parse_cart_response(cart_data)
    assert len(cart_items) == 1
    assert cart_items[0]["quantity"] == 3
