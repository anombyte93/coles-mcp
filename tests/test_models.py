"""Tests for Pydantic data models."""

from coles_mcp.models import Product, ProductDetail, CartItem, Cart


def test_product_model():
    """Test Product model creation and serialization."""
    product = Product(
        name="Test Product",
        price=5.99,
        unit_price="$5.99 per 1kg",
        image_url="https://example.com/image.jpg",
        product_id="123456",
        product_url="/product/123456",
        in_stock=True,
        was_price=7.99,
    )
    data = product.model_dump()

    assert data["name"] == "Test Product"
    assert data["price"] == 5.99
    assert data["unit_price"] == "$5.99 per 1kg"
    assert data["product_id"] == "123456"
    assert data["was_price"] == 7.99


def test_product_detail_model():
    """Test ProductDetail model with extended fields."""
    product = ProductDetail(
        name="Test Product",
        price=5.99,
        product_id="123456",
        product_url="/product/123456",
        description="A great product",
        brand="Test Brand",
        size="500g",
        was_price=7.99,
    )
    data = product.model_dump()

    assert data["name"] == "Test Product"
    assert data["description"] == "A great product"
    assert data["brand"] == "Test Brand"
    assert data["size"] == "500g"


def test_cart_item_model():
    """Test CartItem model."""
    item = CartItem(
        name="Test Item",
        quantity=2,
        price=5.99,
        subtotal=11.98,
        product_id="123456",
        image_url="https://example.com/image.jpg",
    )
    data = item.model_dump()

    assert data["quantity"] == 2
    assert data["subtotal"] == 11.98
    assert data["image_url"] == "https://example.com/image.jpg"


def test_cart_model():
    """Test Cart model with items."""
    cart = Cart(
        items=[
            CartItem(
                name="Item 1",
                quantity=1,
                price=5.99,
                subtotal=5.99,
                product_id="123",
            ),
            CartItem(
                name="Item 2",
                quantity=2,
                price=3.99,
                subtotal=7.98,
                product_id="456",
            ),
        ],
        total=13.97,
        savings=2.00,
        item_count=2,
    )
    data = cart.model_dump()

    assert len(data["items"]) == 2
    assert data["total"] == 13.97
    assert data["savings"] == 2.00
    assert data["item_count"] == 2
