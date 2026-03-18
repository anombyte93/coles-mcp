"""Direct API calls via page.evaluate(fetch()). No DOM parsing needed.

Coles internal APIs are called from INSIDE the browser page context,
inheriting all cookies and anti-bot tokens. Returns clean JSON.

Key feature: subscription_key auto-discovery from Coles homepage JS bundle.
When subscription_key config is empty, scrapes it from Coles homepage on startup.
If any API call returns 401/403, re-discovers the key and retries.
"""

from __future__ import annotations

import json
import re

from playwright.async_api import Page


class ColesAPI:
    """Calls Coles internal REST APIs from inside the browser context."""

    BASE = "https://www.coles.com.au"
    API_BASE = "https://api.coles.com.au"
    MAX_FETCH_RETRIES = 3
    # 429 (rate limit) and 502/503 (infra) are retryable.
    # 401/403 (auth/subscription key) trigger key rediscovery.
    RETRYABLE_CODES = {429, 502, 503}
    AUTH_FAILURE_CODES = {401, 403}

    def __init__(self, page: Page, subscription_key: str = ""):
        self._page = page
        self._subscription_key = subscription_key
        self._auth_verified = False
        self._store_id = "0357"  # Default, should be overridden
        self._fulfillment_store_id = "0357"
        self._shopping_method = "delivery"

    def set_store_context(self, store_id: str, shopping_method: str = "delivery") -> None:
        """Set store context for API calls."""
        self._store_id = store_id
        self._fulfillment_store_id = store_id
        self._shopping_method = shopping_method

    async def _ensure_on_site(self) -> None:
        """Make sure the page is on coles.com.au (needed for fetch context)."""
        url = self._page.url or ""
        if "coles.com.au" not in url:
            await self._page.goto(f"{self.BASE}/", wait_until="domcontentloaded", timeout=30000)

    async def _discover_subscription_key(self) -> str | None:
        """Scrape subscription key from Coles homepage JS bundle.

        Coles frontend includes the subscription key in JS files like:
        "subscription-key":"eae83861d1cd4de6bb9cd8a2cd6f041e"

        Returns the key if found, None otherwise.
        """
        await self._ensure_on_site()
        try:
            # Get all script tags and search for subscription-key pattern
            scripts = await self._page.evaluate("""() => {
                const scripts = Array.from(document.querySelectorAll('script[src]'));
                return scripts.map(s => s.src).filter(Boolean);
            }""")

            # Pattern for subscription-key in JS
            key_pattern = r'subscription-key["\']?\s*:\s*["\']?([a-f0-9]{32})["\']?'

            for script_url in scripts[:20]:  # Check first 20 scripts only
                if script_url and '.js' in script_url:
                    try:
                        response = await self._page.evaluate(f"""async () => {{
                            try {{
                                const r = await fetch('{script_url}', {{credentials: 'include'}});
                                const text = await r.text();
                                return text;
                            }} catch(e) {{
                                return null;
                            }}
                        }}""")

                        if response:
                            match = re.search(key_pattern, response, re.IGNORECASE)
                            if match:
                                return match.group(1)
                    except Exception:
                        continue

            # Fallback: check inline scripts
            inline_scripts = await self._page.evaluate("""() => {
                const scripts = Array.from(document.querySelectorAll('script:not([src])'));
                return scripts.map(s => s.textContent).join('\\n');
            }""")

            if inline_scripts:
                match = re.search(key_pattern, inline_scripts, re.IGNORECASE)
                if match:
                    return match.group(1)

        except Exception:
            pass

        return None

    async def _get_subscription_key(self, force_refresh: bool = False) -> str:
        """Get subscription key, discovering if needed.

        If force_refresh is True or key is empty, re-disccover from homepage.
        """
        if force_refresh or not self._subscription_key:
            discovered = await self._discover_subscription_key()
            if discovered:
                self._subscription_key = discovered
        return self._subscription_key or ""

    async def check_auth(self) -> dict:
        """Check auth state via Coles API.

        Returns {authenticated, is_guest, name, cart_count}.
        """
        await self._ensure_on_site()
        result = await self._page.evaluate("""
            async () => {
                try {
                    const r = await fetch('/api/customer/v1/coles/getuser', {
                        credentials: 'include',
                        headers: {'Accept': 'application/json'}
                    });
                    if (r.status === 401) {
                        return {authenticated: false, is_guest: true};
                    }
                    const d = await r.json();
                    return {
                        authenticated: !!(d && d.customerId),
                        is_guest: !(d && d.customerId),
                        name: d?.firstName || null,
                        email: d?.emailAddress || null,
                    };
                } catch(e) {
                    return {authenticated: false, is_guest: true, error: e.message};
                }
            }
        """)
        self._auth_verified = result.get("authenticated", False)
        return result

    async def _fetch_json(
        self,
        path: str,
        method: str = "GET",
        body: dict | list | None = None,
        use_api_base: bool = False,
    ) -> dict:
        """Execute a fetch() call inside the browser page and return JSON.

        Retries on 401/403 (subscription key rotation) and 429/502/503 (infra).
        Auto-discovers new subscription key on auth failures.
        """
        await self._ensure_on_site()

        # Build URL with subscription key
        subscription_key = await self._get_subscription_key()
        separator = "&" if "?" in path else "?"
        full_path = path
        if subscription_key:
            full_path = f"{path}{separator}subscription-key={subscription_key}"

        base = self.API_BASE if use_api_base else self.BASE
        body_js = f"body: JSON.stringify({json.dumps(body)})," if body is not None else ""
        js = f"""
        async () => {{
            try {{
                const resp = await fetch('{base}{full_path}', {{
                    method: '{method}',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }},
                    {body_js}
                    credentials: 'include'
                }});
                if (!resp.ok) {{
                    return {{ error: resp.status, message: resp.statusText }};
                }}
                return await resp.json();
            }} catch (e) {{
                return {{ error: 'fetch_failed', message: e.message }};
            }}
        }}
        """
        import asyncio as _asyncio

        last_result = None
        for attempt in range(self.MAX_FETCH_RETRIES + 1):  # +1 for auth retry
            last_result = await self._page.evaluate(js)
            error_code = last_result.get("error") if isinstance(last_result, dict) else None

            # Success or non-retryable/non-auth error — return immediately
            if error_code is None:
                return last_result

            if error_code in self.AUTH_FAILURE_CODES:
                # Try to refresh subscription key and retry once
                if attempt == 0:
                    await self._get_subscription_key(force_refresh=True)
                    # Rebuild JS with new key
                    subscription_key = await self._get_subscription_key()
                    separator = "&" if "?" in path else "?"
                    full_path = f"{path}{separator}subscription-key={subscription_key}"
                    js = f"""
                    async () => {{
                        try {{
                            const resp = await fetch('{base}{full_path}', {{
                                method: '{method}',
                                headers: {{
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json'
                                }},
                                {body_js}
                                credentials: 'include'
                            }});
                            if (!resp.ok) {{
                                return {{ error: resp.status, message: resp.statusText }};
                            }}
                            return await resp.json();
                        }} catch (e) {{
                            return {{ error: 'fetch_failed', message: e.message }};
                        }}
                    }}
                    """
                    continue
                else:
                    # Auth failed even after key refresh
                    return last_result

            # Retryable error — exponential backoff (1s, 2s, 4s...)
            if error_code in self.RETRYABLE_CODES:
                if attempt < self.MAX_FETCH_RETRIES:
                    await _asyncio.sleep(2 ** attempt)
                    continue

            # Non-retryable error
            return last_result

        return last_result

    async def search(self, query: str, page_num: int = 1, page_size: int = 24) -> dict:
        """Search products. Returns {items, total}."""
        # Coles search API
        return await self._fetch_json(
            f"/api/customer/v1/coles/products/search/?term={query}&pageNumber={page_num}&pageSize={page_size}",
            "GET",
            use_api_base=True,
        )

    async def product_detail(self, product_id: str) -> dict:
        """Get full product detail. Returns product data."""
        return await self._fetch_json(
            f"/api/customer/v1/coles/products/{product_id}",
            "GET",
            use_api_base=True,
        )

    async def specials(self, category_id: str = "", page_num: int = 1) -> dict:
        """Browse specials. Returns special offers."""
        if category_id:
            path = f"/api/customer/v1/coles/specials?categoryId={category_id}&pageNumber={page_num}"
        else:
            path = f"/api/customer/v1/coles/specials?pageNumber={page_num}"
        return await self._fetch_json(path, "GET", use_api_base=True)

    async def add_to_cart(self, product_id: str, quantity: int = 1) -> dict:
        """Add item to cart. Returns updated cart state."""
        return await self._fetch_json(
            "/api/customer/v1/coles/cart/items",
            "POST",
            {
                "productId": product_id,
                "quantity": quantity,
                "fulfillmentStoreId": self._fulfillment_store_id,
            },
            use_api_base=True,
        )

    async def view_cart(self) -> dict:
        """Get current cart contents."""
        return await self._fetch_json(
            "/api/customer/v1/coles/cart",
            "GET",
            use_api_base=True,
        )

    async def bulk_products(self, product_ids: list[str]) -> dict:
        """Fetch multiple products by ID in one call."""
        ids = ",".join(product_ids)
        return await self._fetch_json(
            f"/api/customer/v1/coles/products/bulk?ids={ids}",
            "GET",
            use_api_base=True,
        )

    async def delivery_setup(self) -> dict:
        """Get current delivery settings."""
        return await self._fetch_json(
            "/api/customer/v1/coles/delivery/setup",
            "GET",
            use_api_base=True,
        )

    async def health_check(self) -> dict:
        """Three-layer health check: CDP → API → Auth. Returns structured status."""
        import time
        result = {}

        # Layer 1: CDP — can we reach the page at all?
        t0 = time.monotonic()
        try:
            await self._ensure_on_site()
            result["cdp"] = {"status": "ok", "latency_ms": round((time.monotonic() - t0) * 1000)}
        except Exception as e:
            result["cdp"] = {"status": "fail", "error": str(e), "latency_ms": round((time.monotonic() - t0) * 1000)}
            result["api"] = {"status": "unknown", "reason": "cdp_down"}
            result["auth"] = {"status": "unknown", "reason": "cdp_down"}
            return result

        # Layer 2: API — does Coles respond to a lightweight fetch?
        t1 = time.monotonic()
        auth_data = await self.check_auth()
        api_latency = round((time.monotonic() - t1) * 1000)

        if "error" in auth_data:
            result["api"] = {"status": "fail", "error": auth_data.get("message", "unknown"), "latency_ms": api_latency}
            result["auth"] = {"status": "unknown", "reason": "api_down"}
            return result

        result["api"] = {"status": "ok", "latency_ms": api_latency}

        # Layer 3: Auth — is this an authenticated session (not guest)?
        if auth_data.get("authenticated"):
            result["auth"] = {
                "status": "ok",
                "name": auth_data.get("name"),
                "email": auth_data.get("email"),
            }
        else:
            result["auth"] = {
                "status": "fail",
                "is_guest": auth_data.get("is_guest", True),
            }

        # Layer 4: Subscription key
        subscription_key = await self._get_subscription_key()
        result["subscription_key"] = {
            "status": "ok" if subscription_key else "missing",
            "discovered": bool(subscription_key),
        }

        return result
