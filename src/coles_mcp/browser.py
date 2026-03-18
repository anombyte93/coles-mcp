"""Browser manager: singleton CDP connection to Brave via Playwright.

Auto-recovery: if Brave CDP is unreachable (ECONNREFUSED), BrowserManager
runs launch-brave-cdp to restart it, then retries the connection.
"""

from __future__ import annotations

import asyncio
import json
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from playwright.async_api import Browser, BrowserContext, Page, async_playwright


class BrowserManager:
    """Singleton managing Playwright CDP connection to Brave on a configurable port.

    Auto-recovery: if connect_over_cdp fails (Brave dead/crashed/reaped),
    launches a new Brave instance via launch-brave-cdp and retries.

    Supports cookie injection for persisting auth sessions across restarts.
    """

    MAX_CONNECT_RETRIES = 2

    def __init__(self, cdp_url: str | None = None):
        self._cdp_url = cdp_url
        self._browser: Browser | None = None
        self._playwright = None
        self._lock = asyncio.Lock()
        self._cookies_injected = False
        self._page: Page | None = None

    def _slot_from_url(self) -> int | None:
        """Extract slot number from CDP URL (port 61000+N → slot N)."""
        match = re.search(r":(\d+)", self._cdp_url)
        if match:
            port = int(match.group(1))
            if 61000 <= port <= 61009:
                return port - 61000
        return None

    async def _relaunch_brave(self) -> bool:
        """Launch Brave CDP via launch-brave-cdp. Returns True if launch succeeded."""
        slot = self._slot_from_url()
        if slot is None:
            return False
        proc = await asyncio.create_subprocess_exec(
            "launch-brave-cdp", str(slot),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        rc = await proc.wait()
        return rc == 0

    async def connect(self) -> Browser:
        """Establish CDP connection with auto-recovery.

        If connect_over_cdp fails (Brave dead), relaunches Brave and retries.
        Resets stale state (page, cookies_injected) on reconnect.
        """
        async with self._lock:
            if self._browser and self._browser.is_connected():
                return self._browser

            last_error = None
            for attempt in range(self.MAX_CONNECT_RETRIES):
                try:
                    if not self._playwright:
                        self._playwright = await async_playwright().start()
                    self._browser = await self._playwright.chromium.connect_over_cdp(self._cdp_url)
                    if attempt > 0:
                        # Reconnected after relaunch — reset stale state
                        self._cookies_injected = False
                        self._page = None
                    return self._browser
                except Exception as e:
                    last_error = e
                    # Clean up stale playwright before retry
                    if self._playwright:
                        try:
                            await self._playwright.stop()
                        except Exception:
                            pass
                        self._playwright = None
                    self._browser = None
                    self._cookies_injected = False
                    self._page = None

                    if attempt < self.MAX_CONNECT_RETRIES - 1:
                        await self._relaunch_brave()
                        await asyncio.sleep(2)

            raise last_error

    async def _get_context(self) -> BrowserContext:
        """Get the first browser context (reuses existing session/cookies)."""
        browser = await self.connect()
        contexts = browser.contexts
        if not contexts:
            ctx = await browser.new_context()
        else:
            ctx = contexts[0]
        # Inject saved auth cookies on first access
        if not self._cookies_injected:
            await self._inject_auth_cookies(ctx)
            self._cookies_injected = True
        return ctx

    async def _inject_auth_cookies(self, ctx: BrowserContext) -> None:
        """Load saved auth cookies from config and inject into context.

        This allows MFA bypass: saved cookies tell Coles this is a
        recognized device/session.
        """
        cookie_file = Path(__file__).parent.parent.parent / "config" / "auth-cookies.json"
        if not cookie_file.exists():
            return
        try:
            with open(cookie_file) as f:
                cookies = json.load(f)
            if cookies:
                await ctx.add_cookies(cookies)
        except Exception:
            pass  # Non-fatal — will just require manual login

    async def export_auth_cookies(self) -> None:
        """Export current auth cookies to config/auth-cookies.json for persistence."""
        ctx = await self._get_context()
        cookies = await ctx.cookies([
            "https://www.coles.com.au",
            "https://api.coles.com.au",
        ])
        # Coles uses various auth cookies — save all that look relevant
        auth_names = {"flybuys", "session", "auth", "token", "jwt"}
        auth_cookies = [c for c in cookies if any(name in c["name"].lower() for name in auth_names)]
        cookie_file = Path(__file__).parent.parent.parent / "config" / "auth-cookies.json"
        with open(cookie_file, "w") as f:
            json.dump(auth_cookies, f, indent=2)

    async def get_page(self) -> Page:
        """Get a persistent page. Reuses the same tab across all tool calls.

        No tab opening/closing — navigates within a single tab.
        This prevents visible tab flashing and mouse takeover.
        """
        context = await self._get_context()
        if self._page and not self._page.is_closed():
            return self._page
        # Find an existing page or create one
        pages = context.pages
        if pages:
            self._page = pages[0]
        else:
            self._page = await context.new_page()
        return self._page

    @asynccontextmanager
    async def page(self) -> AsyncIterator[Page]:
        """Context manager: yields the persistent page. Does NOT close it on exit."""
        p = await self.get_page()
        yield p
        # Intentionally NOT closing — we reuse this tab

    async def health_check(self) -> bool:
        """Check if CDP connection is alive."""
        try:
            if self._browser and self._browser.is_connected():
                return True
            return False
        except Exception:
            return False

    async def close(self) -> None:
        """Shut down the connection."""
        if self._browser:
            # Don't close the browser itself — it's external (Brave)
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
