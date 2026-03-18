"""Anti-detection system: human-like delays, throttling, and interaction patterns."""

from __future__ import annotations

import asyncio
import random
import time


async def random_delay(min_s: float = 0.5, max_s: float = 2.5) -> None:
    """Sleep for a random duration using gaussian distribution clamped to [min_s, max_s]."""
    mean = (min_s + max_s) / 2
    stddev = (max_s - min_s) / 4
    delay = random.gauss(mean, stddev)
    delay = max(min_s, min(max_s, delay))
    await asyncio.sleep(delay)


class Throttle:
    """Token bucket rate limiter."""

    def __init__(self, max_per_minute: int = 30):
        self.max_per_minute = max_per_minute
        self._tokens = float(max_per_minute)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(
                self.max_per_minute,
                self._tokens + elapsed * (self.max_per_minute / 60.0),
            )
            self._last_refill = now

            if self._tokens < 1.0:
                wait_time = (1.0 - self._tokens) / (self.max_per_minute / 60.0)
                await asyncio.sleep(wait_time)
                self._tokens = 0.0
                self._last_refill = time.monotonic()
            else:
                self._tokens -= 1.0


class AntiDetection:
    """Wraps browser interactions with human-like timing."""

    def __init__(
        self,
        min_delay: float = 0.5,
        max_delay: float = 2.5,
        max_requests_per_minute: int = 30,
        inter_key_delay_min: float = 0.05,
        inter_key_delay_max: float = 0.15,
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.inter_key_delay_min = inter_key_delay_min
        self.inter_key_delay_max = inter_key_delay_max
        self.throttle = Throttle(max_requests_per_minute)

    async def wait(self) -> None:
        """Apply random delay + throttle before an action."""
        await self.throttle.acquire()
        await random_delay(self.min_delay, self.max_delay)

    async def type_like_human(self, page, selector: str, text: str) -> None:
        """Type text character by character with random inter-key delays."""
        locator = page.locator(selector)
        await locator.click()
        for char in text:
            await page.keyboard.type(char)
            delay = random.uniform(self.inter_key_delay_min, self.inter_key_delay_max)
            await asyncio.sleep(delay)

    async def scroll_to(self, page, selector: str) -> None:
        """Smooth scroll to an element before interacting."""
        await page.locator(selector).scroll_into_view_if_needed()
        await random_delay(0.2, 0.5)
