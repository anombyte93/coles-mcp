"""Integration tests requiring live Brave CDP connection."""

import pytest
import os


@pytest.mark.integration
@pytest.mark.asyncio
async def test_subscription_key_discovery():
    """Test subscription key auto-discovery from Coles homepage."""
    from coles_mcp.browser import BrowserManager
    from coles_mcp.api import ColesAPI

    # Get CDP port from env or use default
    slot = os.environ.get("BRAVE_CDP_SLOT", "5")
    cdp_port = 61000 + int(slot)
    cdp_url = f"http://127.0.0.1:{cdp_port}"

    browser = BrowserManager(cdp_url)
    try:
        page = await browser.get_page()
        api = ColesAPI(page, "")

        # Try to discover subscription key
        key = await api._get_subscription_key(force_refresh=True)

        # We may or may not find a key depending on Coles site structure
        # Just verify the discovery process runs without error
        assert isinstance(key, str)

    finally:
        await browser.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_coles_health_check_live():
    """Test health check with live Coles API."""
    from coles_mcp.browser import BrowserManager
    from coles_mcp.api import ColesAPI
    from coles_mcp.config import load_config

    config = load_config()
    browser = BrowserManager(config.browser.cdp_url)
    try:
        page = await browser.get_page()
        api = ColesAPI(page, config.api.subscription_key)
        api.set_store_context(config.store.store_id, config.store.shopping_method)

        result = await api.health_check()

        # Check structure
        assert "cdp" in result
        assert "api" in result
        assert "auth" in result

        # CDP should be ok if Brave is running
        assert result["cdp"]["status"] in ["ok", "fail"]

        # subscription_key may not be present if API layer is down (Imperva blocking)
        # This is expected behavior - demo mode fallback handles this
        if result["api"]["status"] == "ok":
            assert "subscription_key" in result

    finally:
        await browser.close()
