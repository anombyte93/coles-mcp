"""FastMCP server exposing Coles grocery tools via internal API calls.

Architecture: Playwright CDP → page.evaluate(fetch()) → Coles REST APIs → JSON.
The browser context provides cookies and anti-bot tokens.
No DOM parsing — all data from structured API responses.

Key feature: subscription_key auto-discovery. When config subscription_key is empty,
scrapes it from Coles homepage JS bundle on startup. If any API call returns
401/403, re-discovers the key and retries.

Auth model: Cookie-first. BrowserManager injects saved cookies on connect.
Every auth-requiring tool calls _ensure_auth() which verifies auth state.
"""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP

from coles_mcp.anti_detection import AntiDetection
from coles_mcp.api import ColesAPI
from coles_mcp.browser import BrowserManager
from coles_mcp.config import load_config
from coles_mcp.models import Product, ProductDetail, CartItem, Cart

_config = load_config()
_browser = BrowserManager(_config.browser.cdp_url)
_anti = AntiDetection(
    min_delay=_config.anti_detection.min_delay,
    max_delay=_config.anti_detection.max_delay,
    max_requests_per_minute=_config.anti_detection.max_requests_per_minute,
    inter_key_delay_min=_config.anti_detection.inter_key_delay_min,
    inter_key_delay_max=_config.anti_detection.inter_key_delay_max,
)
_tool_lock = asyncio.Lock()

BASE_URL = f"https://www.{_config.site}"

mcp = FastMCP("coles-mcp")


def _product_from_api(p: dict) -> dict:
    """Convert a Coles API product object to our Product model."""
    return Product(
        name=p.get("name", ""),
        price=p.get("price") or 0,
        unit_price=p.get("unitPrice"),
        image_url=p.get("imageUrl"),
        product_id=str(p.get("id", "")),
        product_url=p.get("productUrl", ""),
        in_stock=p.get("inStock", True),
        was_price=p.get("wasPrice"),
    ).model_dump()


async def _ensure_auth(api: ColesAPI) -> dict:
    """Hard auth gate. Called before any auth-requiring operation.

    Flow: check auth → if authenticated, return immediately →
    if guest, return guidance for manual login.

    Returns auth state dict. Caller should check ['authenticated'].
    """
    auth = await api.check_auth()
    if auth.get("authenticated"):
        return auth

    # Guest session — MCP server can't interactively prompt for credentials.
    # Return guidance so the operator knows they need to login.
    return {
        "authenticated": False,
        "is_guest": True,
        "message": f"Session expired. Please login manually in Brave at {BASE_URL}",
    }


@mcp.tool()
async def coles_health_check() -> dict:
    """Verify Brave CDP, Coles API, auth state, and subscription key. No auth required.

    Returns structured status for four layers:
    - cdp: Brave browser reachable via CDP
    - api: Coles API responds
    - auth: Session is authenticated (not guest)
    - subscription_key: Subscription key discovered and valid
    Each layer includes status (ok/fail) and latency_ms.
    """
    async with _tool_lock:
        try:
            page = await _browser.get_page()
            api = ColesAPI(page, _config.api.subscription_key)
            api.set_store_context(_config.store.store_id, _config.store.shopping_method)
            return await api.health_check()
        except Exception as e:
            return {
                "cdp": {"status": "fail", "error": str(e)},
                "api": {"status": "unknown", "reason": "cdp_down"},
                "auth": {"status": "unknown", "reason": "cdp_down"},
                "subscription_key": {"status": "unknown", "reason": "cdp_down"},
            }


@mcp.tool()
async def coles_login() -> dict:
    """Check login status via real auth state (not cart/API accessibility).

    Checks customer API — if customerId present, user is logged in.
    Returns current auth status.
    """
    async with _tool_lock:
        try:
            page = await _browser.get_page()
            api = ColesAPI(page, _config.api.subscription_key)
            api.set_store_context(_config.store.store_id, _config.store.shopping_method)
            auth = await api.check_auth()
            if auth.get("authenticated"):
                return {
                    "success": True,
                    "message": f"Logged in as {auth['name']} ({auth['email']})",
                }
            return {
                "success": False,
                "is_guest": auth.get("is_guest", True),
                "message": f"Not authenticated (guest session). Please login manually at {BASE_URL}",
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


@mcp.tool()
async def coles_login_with_credentials(email: str, password: str) -> dict:
    """Log in to Coles via Flybuys.

    Args:
        email: Flybuys email
        password: Account password
    """
    async with _tool_lock:
        await _anti.wait()
        page = await _browser.get_page()

        # Navigate to login page
        await page.goto(f"{BASE_URL}/account/login", wait_until="domcontentloaded", timeout=30000)
        await _anti.wait()

        # Check if already logged in
        if "account" in page.url and "login" not in page.url:
            return {"success": True, "message": "Already logged in"}

        # Fill email
        try:
            await page.wait_for_selector('input[type="email"], input[name="email"]', timeout=10000)
            await _anti.type_like_human(page, 'input[type="email"], input[name="email"]', email)
            await _anti.wait()
        except Exception:
            return {"success": False, "message": "Email input not found"}

        # Fill password
        try:
            await _anti.type_like_human(page, 'input[type="password"], input[name="password"]', password)
            await _anti.wait()
        except Exception:
            return {"success": False, "message": "Password input not found"}

        # Submit form
        try:
            await page.evaluate("""() => {
                const btn = document.querySelector('button[type="submit"], button[name="login"], button[name="submit"]');
                if (btn) btn.click();
            }""")
            await _anti.wait()
        except Exception:
            return {"success": False, "message": "Submit button not found"}

        # Wait for navigation
        try:
            await page.wait_for_url(f"**{_config.site}**", timeout=20000)
        except Exception:
            pass

        # Check for MFA
        if "mfa" in page.url.lower() or "verification" in page.url.lower() or "code" in page.url.lower():
            return {"success": False, "requires_mfa": True, "message": "MFA required — solve manually in Brave"}

        # Export cookies
        try:
            await _browser.export_auth_cookies()
        except Exception:
            pass  # Non-fatal

        return {"success": True, "message": "Login successful"}


@mcp.tool()
async def coles_search(query: str, page_num: int = 1) -> dict:
    """Search for products on Coles. Returns structured product data.

    Args:
        query: Search term (e.g., 'milk', 'bread', 'eggs')
        page_num: Page number for pagination (default: 1)
    """
    async with _tool_lock:
        await _anti.wait()
        page = await _browser.get_page()
        api = ColesAPI(page, _config.api.subscription_key)
        api.set_store_context(_config.store.store_id, _config.store.shopping_method)
        data = await api.search(query, page_num)

        if "error" in data:
            return data

        products = []
        for p in data.get("items", []):
            if p.get("id"):
                products.append(_product_from_api(p))

        return {
            "results": products,
            "total_count": data.get("total", len(products)),
            "page": page_num,
            "query": query,
        }


@mcp.tool()
async def coles_product_detail(product_id: str) -> dict:
    """Get detailed product information by product ID.

    Args:
        product_id: Coles product ID (e.g., '123456')
    """
    async with _tool_lock:
        await _anti.wait()
        page = await _browser.get_page()
        api = ColesAPI(page, _config.api.subscription_key)
        api.set_store_context(_config.store.store_id, _config.store.shopping_method)
        data = await api.product_detail(product_id)

        if "error" in data:
            return data

        return ProductDetail(
            name=data.get("name", ""),
            price=data.get("price") or 0,
            unit_price=data.get("unitPrice"),
            image_url=data.get("imageUrl"),
            product_id=str(data.get("id", product_id)),
            product_url=data.get("productUrl", ""),
            description=data.get("description"),
            nutrition=data.get("nutrition"),
            brand=data.get("brand"),
            size=data.get("size"),
            was_price=data.get("wasPrice"),
        ).model_dump()


@mcp.tool()
async def coles_specials(category_id: str = "", page_num: int = 1) -> dict:
    """Browse current specials and promotions.

    Args:
        category_id: Optional category ID to filter specials
        page_num: Page number for pagination (default: 1)
    """
    async with _tool_lock:
        await _anti.wait()
        page = await _browser.get_page()
        api = ColesAPI(page, _config.api.subscription_key)
        api.set_store_context(_config.store.store_id, _config.store.shopping_method)
        data = await api.specials(category_id, page_num)

        if "error" in data:
            return data

        products = []
        for p in data.get("items", []):
            if p.get("id"):
                products.append(_product_from_api(p))

        return {
            "products": products,
            "total_count": data.get("total", len(products)),
            "page": page_num,
            "category_id": category_id,
        }


@mcp.tool()
async def coles_add_to_cart(product_id: str, quantity: int = 1) -> dict:
    """Add a product to cart by product ID. Requires authentication.

    Args:
        product_id: Coles product ID
        quantity: Number to add (default: 1)
    """
    async with _tool_lock:
        await _anti.wait()
        page = await _browser.get_page()
        api = ColesAPI(page, _config.api.subscription_key)
        api.set_store_context(_config.store.store_id, _config.store.shopping_method)

        auth = await _ensure_auth(api)
        if not auth.get("authenticated"):
            return {"success": False, **auth}

        data = await api.add_to_cart(product_id, quantity)

        if "error" in data:
            return data

        return {
            "success": True,
            "message": f"Added {quantity}x product {product_id} to cart",
            "cart": data,
        }


@mcp.tool()
async def coles_view_cart() -> dict:
    """View current cart contents and total. Requires authentication."""
    async with _tool_lock:
        await _anti.wait()
        page = await _browser.get_page()
        api = ColesAPI(page, _config.api.subscription_key)
        api.set_store_context(_config.store.store_id, _config.store.shopping_method)

        auth = await _ensure_auth(api)
        if not auth.get("authenticated"):
            return {"success": False, **auth}

        data = await api.view_cart()

        if "error" in data:
            return data

        items = []
        for item in data.get("items", []):
            price = item.get("price", item.get("unitPrice", 0))
            quantity = item.get("quantity", 0)
            subtotal = price * quantity if price else item.get("totalPrice", 0)

            items.append(CartItem(
                name=item.get("name", ""),
                quantity=quantity,
                price=price,
                subtotal=subtotal,
                product_id=str(item.get("id", "")),
                image_url=item.get("imageUrl"),
            ).model_dump())

        return Cart(
            items=items,
            total=data.get("total", 0),
            savings=data.get("savings", 0),
            item_count=len(items),
        ).model_dump()


@mcp.tool()
async def coles_bulk_products(product_ids: list[str]) -> dict:
    """Fetch multiple products by ID in one call.

    Args:
        product_ids: List of Coles product IDs (e.g., ['123456', '789012'])
    """
    async with _tool_lock:
        await _anti.wait()
        page = await _browser.get_page()
        api = ColesAPI(page, _config.api.subscription_key)
        api.set_store_context(_config.store.store_id, _config.store.shopping_method)
        data = await api.bulk_products(product_ids)

        if "error" in data:
            return data

        products = []
        for p in data.get("items", []):
            if p.get("id"):
                products.append(_product_from_api(p))

        return {
            "products": products,
            "total_count": len(products),
        }


@mcp.tool()
async def coles_delivery_setup() -> dict:
    """Check current delivery settings from the API. Requires authentication."""
    async with _tool_lock:
        await _anti.wait()
        page = await _browser.get_page()
        api = ColesAPI(page, _config.api.subscription_key)
        api.set_store_context(_config.store.store_id, _config.store.shopping_method)

        auth = await _ensure_auth(api)
        if not auth.get("authenticated"):
            return {"success": False, **auth}

        data = await api.delivery_setup()

        if "error" in data:
            return data

        return {
            "success": True,
            "delivery_info": data,
        }


@mcp.tool()
async def coles_select_time_slot(slot_text: str) -> dict:
    """Select a delivery time slot. Requires browser interaction.

    Args:
        slot_text: Text of the time slot (e.g., 'Today', 'Tomorrow', 'Direct to boot Now')
    """
    async with _tool_lock:
        await _anti.wait()
        page = await _browser.get_page()
        await page.goto(f"{BASE_URL}/", wait_until="domcontentloaded", timeout=30000)
        await _anti.wait()

        try:
            # Look for time slot selection button
            time_btn = page.locator("button:has-text('Select a time'), button:has-text('Choose Time'), button:has-text('View available')").first
            await time_btn.click(timeout=5000)
            await _anti.wait()
        except Exception:
            return {"success": False, "message": "Could not open time slot picker"}

        try:
            slot_btn = page.locator(f"text='{slot_text}'").first
            await slot_btn.click(timeout=5000)
            await _anti.wait()

            confirm = page.locator("button:has-text('Reserve'), button:has-text('Done'), button:has-text('Confirm')").first
            try:
                await confirm.click(timeout=3000)
            except Exception:
                pass

            return {"success": True, "message": f"Selected: {slot_text}"}
        except Exception as e:
            return {"success": False, "message": f"Could not find slot '{slot_text}': {e}"}


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
