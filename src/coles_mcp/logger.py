"""Logging utilities for Coles MCP server."""

from __future__ import annotations

import logging
import sys
from typing import Any

# Structured logging for MCP server
logger = logging.getLogger("coles-mcp")


def setup_logging(level: int | str = logging.INFO) -> None:
    """Configure logging for the MCP server.

    Args:
        level: Logging level (default: INFO)
    """
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)


def log_api_call(method: str, url: str, status: int | None = None) -> None:
    """Log an API call with context.

    Args:
        method: HTTP method
        url: Request URL
        status: Response status code (if available)
    """
    status_str = f" - {status}" if status else ""
    logger.debug(f"API: {method} {url}{status_str}")


def log_subscription_key_event(event: str, source: str = "") -> None:
    """Log subscription key events.

    Args:
        event: Event description (e.g., "discovered", "refreshed", "cached")
        source: Source of the key (e.g., "config", "homepage", "cache")
    """
    source_str = f" from {source}" if source else ""
    logger.info(f"Subscription key {event}{source_str}")


def log_auth_event(event: str, details: str | None = None) -> None:
    """Log authentication events.

    Args:
        event: Event description (e.g., "login_success", "logout", "session_expired")
        details: Additional details
    """
    details_str = f" - {details}" if details else ""
    logger.info(f"Auth: {event}{details_str}")


def log_error(
    context: str, error: Exception, extra: dict[str, Any] | None = None
) -> None:
    """Log an error with context.

    Args:
        context: Where the error occurred
        error: The exception
        extra: Additional context data
    """
    extra_str = f" - {extra}" if extra else ""
    logger.error(f"{context}: {type(error).__name__}: {error}{extra_str}")
