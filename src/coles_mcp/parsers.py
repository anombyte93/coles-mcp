"""Response parsers for Coles API data.

Coles APIs return various response formats. These parsers normalize
the data into our standard Product/ProductDetail/Cart models.
"""

from __future__ import annotations

from typing import Any

from coles_mcp.models import Product, ProductDetail, CartItem


def parse_search_response(data: dict[str, Any]) -> list[dict]:
    """Parse search API response into Product models.

    Coles search returns: {items: [...], total: N}
    Each item may have different field names.
    """
    products = []
    for item in data.get("items", []):
        # Handle various field name variations
        product = Product(
            name=item.get("name") or item.get("productName") or "",
            price=item.get("price") or item.get("salePrice") or item.get("listedPrice") or 0,
            unit_price=item.get("unitPrice") or item.get("pricePerUnit"),
            image_url=item.get("imageUrl") or item.get("image") or item.get("thumbnail"),
            product_id=str(item.get("id") or item.get("productId") or item.get("stockcode") or ""),
            product_url=item.get("productUrl") or item.get("url") or "",
            in_stock=item.get("inStock") is not False,
            was_price=item.get("wasPrice") or item.get("originalPrice") or item.get("listPrice"),
        ).model_dump()
        products.append(product)
    return products


def parse_product_detail(data: dict[str, Any]) -> dict:
    """Parse product detail API response into ProductDetail model.

    Coles product detail returns full product info with nutrition,
    ratings, etc.
    """
    item = data.get("product") or data.get("item") or data
    return ProductDetail(
        name=item.get("name") or "",
        price=item.get("price") or item.get("salePrice") or 0,
        unit_price=item.get("unitPrice") or item.get("pricePerUnit"),
        image_url=item.get("imageUrl") or item.get("image"),
        product_id=str(item.get("id") or item.get("productId") or ""),
        product_url=item.get("productUrl") or item.get("url") or "",
        description=item.get("description") or item.get("longDescription"),
        nutrition=item.get("nutrition") or item.get("nutritionalInfo"),
        brand=item.get("brand") or item.get("manufacturer"),
        size=item.get("size") or item.get("packageSize"),
        was_price=item.get("wasPrice") or item.get("originalPrice"),
        ratings=item.get("rating") or item.get("averageRating"),
        review_count=item.get("reviewCount") or item.get("numberOfReviews"),
    ).model_dump()


def parse_cart_response(data: dict[str, Any]) -> list[dict]:
    """Parse cart API response into CartItem models.

    Coles cart returns: {items: [...], total: N, savings: N}
    """
    items = []
    for item in data.get("items", data.get("cartItems", [])):
        # Handle various field name variations
        price = item.get("price") or item.get("salePrice") or item.get("listedPrice") or 0
        quantity = item.get("quantity") or item.get("qty") or 0
        subtotal = item.get("subtotal") or item.get("totalPrice") or (price * quantity)

        cart_item = CartItem(
            name=item.get("name") or item.get("productName") or "",
            quantity=quantity,
            price=price,
            subtotal=subtotal,
            product_id=str(item.get("id") or item.get("productId") or ""),
            image_url=item.get("imageUrl") or item.get("image"),
        ).model_dump()
        items.append(cart_item)
    return items
