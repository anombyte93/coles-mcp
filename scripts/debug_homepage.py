#!/usr/bin/env python3
"""Debug script to inspect Coles homepage for subscription key patterns."""

import asyncio
import re
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright


async def debug_homepage() -> None:
    """Inspect Coles homepage to find subscription key patterns."""
    print("=" * 60)
    print("Coles Homepage Debug - Subscription Key Patterns")
    print("=" * 60)
    print()

    url = "https://www.coles.com.au"

    async with async_playwright() as p:
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"📄 Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print("   ✓ Page loaded")

        # Get all script tags
        print("\n🔍 Searching for subscription key patterns...")

        # Pattern 1: Original pattern from api.py
        pattern1 = r'subscription-key["\']?\s*:\s*["\']?([a-f0-9]{32})["\']?'
        # Pattern 2: Alternative variations
        pattern2 = r'subscriptionKey["\']?\s*:\s*["\']?([a-f0-9]{32})["\']?'
        pattern3 = r'["\']subscription-key["\']\s*:\s*["\']([a-f0-9]{32})["\']'
        pattern4 = r'Ocp-Apim-Subscription-Key["\']?\s*:\s*["\']?([a-f0-9]{32})["\']?'

        patterns = [
            ("Original (subscription-key:)", pattern1),
            ("CamelCase (subscriptionKey:)", pattern2),
            ("Quoted key", pattern3),
            ("Ocp-Apim header", pattern4),
        ]

        # Check inline scripts
        content = await page.content()
        print(f"\n📊 Page HTML size: {len(content)} characters")

        for name, pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"\n✓ Pattern '{name}' found {len(matches)} matches:")
                for i, match in enumerate(matches[:3], 1):  # Show first 3
                    print(f"   {i}. {match[:8]}...{match[-8:]}")
            else:
                print(f"   ✗ Pattern '{name}': no matches")

        # Check external scripts
        print("\n📜 Checking external scripts...")
        scripts = await page.query_selector_all("script[src]")

        for i, script in enumerate(scripts[:5], 1):  # Check first 5 scripts
            src = await script.get_attribute("src")
            if src:
                print(f"\n   {i}. {src[:80]}")
                # Try to fetch script content
                try:
                    if src.startswith("http"):
                        response = await page.request.get(src)
                        script_content = await response.body()
                        script_text = script_content.decode("utf-8", errors="ignore")

                        for name, pattern in patterns:
                            matches = re.findall(pattern, script_text, re.IGNORECASE)
                            if matches:
                                print(f"      ✓ Pattern '{name}' found: {matches[0][:8]}...{matches[0][-8:]}")
                                break
                except Exception as e:
                    print(f"      ✗ Error fetching: {e}")

        # Look for API base URLs
        print("\n🌐 Looking for API base URLs...")
        api_patterns = [
            r"https://api\.coles\.com\.au",
            r"coles\.au\.auth\.apigee\.net",
            r"api\.coles\.com\.au",
        ]

        for api_pattern in api_patterns:
            matches = re.findall(api_pattern, content, re.IGNORECASE)
            if matches:
                print(f"   ✓ Found: {api_pattern}")

        # Look for any 32-char hex strings (potential keys)
        print("\n🔑 Looking for 32-char hex strings...")
        hex_pattern = r'\b[a-f0-9]{32}\b'
        hex_matches = re.findall(hex_pattern, content, re.IGNORECASE)
        if hex_matches:
            print(f"   Found {len(hex_matches)} potential keys:")
            for i, match in enumerate(hex_matches[:5], 1):
                print(f"   {i}. {match}")
        else:
            print("   No 32-char hex strings found")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_homepage())
