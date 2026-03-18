"""Pydantic data models for Coles product and cart data."""

from __future__ import annotations

from pydantic import BaseModel


class Product(BaseModel):
    name: str
    price: float
    unit_price: str | None = None
    image_url: str | None = None
    product_id: str
    product_url: str
    in_stock: bool = True
    was_price: float | None = None  # For specials/comparison


class ProductDetail(Product):
    description: str | None = None
    nutrition: dict | None = None
    ratings: float | None = None
    review_count: int | None = None
    brand: str | None = None
    size: str | None = None


class CartItem(BaseModel):
    name: str
    quantity: int
    price: float
    subtotal: float
    product_id: str
    image_url: str | None = None


class Cart(BaseModel):
    items: list[CartItem]
    total: float
    savings: float = 0.0
    item_count: int = 0
