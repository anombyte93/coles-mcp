"""Tests for MCP server tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_coles_health_check_mock(mock_page):
    """Test coles_health_check with mocked browser."""
    # Mock the health check response
    mock_page.evaluate.return_value = {
        "authenticated": False,
        "is_guest": True,
    }

    # Mock BrowserManager and ColesAPI
    with patch('coles_mcp.server._browser') as mock_browser:
        mock_browser.get_page = AsyncMock(return_value=mock_page)

        with patch('coles_mcp.server.ColesAPI') as mock_api_class:
            mock_api = AsyncMock()
            mock_api.health_check = AsyncMock(return_value={
                "cdp": {"status": "ok"},
                "api": {"status": "ok"},
                "auth": {"authenticated": False, "is_guest": True},
                "subscription_key": {"status": "ok"},
            })
            mock_api_class.return_value = mock_api

            from coles_mcp import server
            # Reload to get patched modules
            import importlib
            importlib.reload(server)

            result = await server.coles_health_check()

            # Should return a dict with cdp status
            assert "cdp" in result
            assert result["cdp"]["status"] == "ok"


@pytest.mark.asyncio
async def test_coles_login_mock(mock_page):
    """Test coles_login with mocked browser."""
    # Mock guest session response
    mock_page.evaluate.return_value = {
        "authenticated": False,
        "is_guest": True,
    }

    # Mock BrowserManager and ColesAPI
    with patch('coles_mcp.server._browser') as mock_browser:
        mock_browser.get_page = AsyncMock(return_value=mock_page)

        with patch('coles_mcp.server.ColesAPI') as mock_api_class:
            mock_api = AsyncMock()
            mock_api.check_auth = AsyncMock(return_value={
                "authenticated": False,
                "is_guest": True,
            })
            mock_api.set_store_context = MagicMock()
            mock_api_class.return_value = mock_api

            from coles_mcp import server
            import importlib
            importlib.reload(server)

            result = await server.coles_login()

            assert "success" in result
            assert isinstance(result["success"], bool)


@pytest.mark.asyncio
async def test_coles_search_mock(mock_page):
    """Test coles_search with mocked browser."""
    # Mock search response
    mock_page.evaluate.return_value = {
        "items": [
            {
                "id": "123456",
                "name": "Test Product",
                "price": 5.99,
                "unitPrice": "$5.99 each",
                "imageUrl": "https://example.com/image.jpg",
                "productUrl": "/product/123456",
                "inStock": True,
            }
        ],
        "total": 1,
    }

    # Mock BrowserManager and ColesAPI
    with patch('coles_mcp.server._browser') as mock_browser:
        mock_browser.get_page = AsyncMock(return_value=mock_page)

        with patch('coles_mcp.server.ColesAPI') as mock_api_class:
            mock_api = AsyncMock()
            mock_api.search = AsyncMock(return_value={
                "items": [
                    {
                        "id": "123456",
                        "name": "Test Product",
                        "price": 5.99,
                        "unitPrice": "$5.99 each",
                        "imageUrl": "https://example.com/image.jpg",
                        "productUrl": "/product/123456",
                        "inStock": True,
                    }
                ],
                "total": 1,
            })
            mock_api.set_store_context = MagicMock()
            mock_api_class.return_value = mock_api

            with patch('coles_mcp.server._anti') as mock_anti:
                mock_anti.wait = AsyncMock()

                from coles_mcp import server
                import importlib
                importlib.reload(server)

                result = await server.coles_search("milk")

                assert "results" in result
                assert isinstance(result["results"], list)
