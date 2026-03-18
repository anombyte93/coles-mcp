#!/usr/bin/env python3
"""Test script to verify subscription key discovery from Coles homepage."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from coles_mcp.api import ColesAPI
from coles_mcp.browser import BrowserManager
from coles_mcp.config import load_config
from coles_mcp.logger import setup_logging, log_subscription_key_event, log_error


async def test_subscription_key_discovery() -> bool:
    """Test subscription key auto-discovery.

    Returns:
        True if discovery successful, False otherwise
    """
    setup_logging()
    config = load_config()

    print(f"🔍 Testing subscription key discovery from Coles homepage...")
    print(f"   Target: {config.api.base_url}")
    print()

    browser = BrowserManager(config.browser.cdp_url)

    try:
        # Connect to Brave CDP
        print("📡 Connecting to Brave CDP...")
        page = await browser.get_page()
        print("   ✓ Connected")

        # Create API instance with empty subscription key
        api = ColesAPI(page, "")

        # Test discovery
        print("\n🔑 Discovering subscription key...")
        key = await api._discover_subscription_key()

        if key:
            print(f"   ✓ Discovered: {key[:8]}...{key[-8:]}")
            print(f"   ✓ Full key: {key}")
            log_subscription_key_event("discovered", "homepage")

            # Verify key format (32 hex chars)
            if len(key) == 32 and all(c in "0123456789abcdef" for c in key):
                print("   ✓ Key format valid (32 hex characters)")
                return True
            else:
                print(f"   ✗ Key format invalid (expected 32 hex chars, got {len(key)})")
                return False
        else:
            print("   ✗ No subscription key found")
            log_error("Subscription key discovery", Exception("Key not found in page sources"))
            return False

    except Exception as e:
        print(f"   ✗ Error: {e}")
        log_error("Subscription key test", e)
        return False
    finally:
        print("\n🧹 Cleaning up...")
        # Keep browser connection for potential reuse


async def test_api_with_discovered_key() -> bool:
    """Test API call with auto-discovered subscription key.

    Returns:
        True if API call successful, False otherwise
    """
    setup_logging()
    config = load_config()

    print(f"\n🌐 Testing API call with discovered subscription key...")

    browser = BrowserManager(config.browser.cdp_url)

    try:
        page = await browser.get_page()
        api = ColesAPI(page, "")  # Empty key triggers auto-discovery
        api.set_store_context(config.store.store_id, config.store.shopping_method)

        # Test a simple API call (health check or search)
        print("   Calling Coles API...")
        result = await api.search("milk", page_num=1)

        if "error" in result:
            print(f"   ✗ API error: {result['error']}")
            return False

        total = result.get("total", 0)
        items = result.get("items", [])
        print(f"   ✓ API call successful")
        print(f"   ✓ Found {total} results, {len(items)} items returned")

            # Show first product name if available
        if items and len(items) > 0:
            first_item = items[0]
            name = first_item.get("name") or first_item.get("productName", "Unknown")
            print(f"   ✓ First result: {name}")

        return True

    except Exception as e:
        print(f"   ✗ Error: {e}")
        log_error("API test", e)
        return False


async def main() -> int:
    """Run all subscription key tests.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("=" * 60)
    print("Coles MCP - Subscription Key Discovery Test")
    print("=" * 60)
    print()

    # Test 1: Key discovery
    discovery_ok = await test_subscription_key_discovery()

    # Test 2: API call with discovered key
    api_ok = await test_api_with_discovered_key()

    print()
    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    print(f"  Discovery: {'✓ PASS' if discovery_ok else '✗ FAIL'}")
    print(f"  API Test:  {'✓ PASS' if api_ok else '✗ FAIL'}")
    print()

    if discovery_ok and api_ok:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
