"""Shared test fixtures for coles-mcp."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from coles_mcp.api import ColesAPI

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def mock_page():
    """Mock Playwright page object for unit tests."""
    page = AsyncMock()
    page.evaluate = AsyncMock()
    page.goto = AsyncMock()
    page.locator = MagicMock()
    page.url = "https://www.coles.com.au/"
    return page


@pytest.fixture
def mock_api(mock_page):
    """Mock ColesAPI with a mock page."""
    api = ColesAPI(mock_page, "")
    return api
