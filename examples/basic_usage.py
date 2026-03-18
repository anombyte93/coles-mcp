#!/usr/bin/env python3
"""Example usage of Coles MCP server tools.

This script demonstrates how to use the Coles MCP tools
when the server is running.
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    """Run example Coles MCP tool calls."""
    # Connect to the Coles MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "coles_mcp.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            print("=" * 60)
            print("Coles MCP Server - Example Usage")
            print("=" * 60)
            print()

            # Example 1: Health Check
            print("1. Health Check")
            print("-" * 40)
            result = await session.call_tool("coles_health_check", {})
            print(f"CDP Status: {result[0].content['cdp']['status']}")
            print(f"API Status: {result[0].content['api']['status']}")
            print(f"Auth Status: {result[0].content['auth']['status']}")
            print()

            # Example 2: Search for products
            print("2. Product Search")
            print("-" * 40)
            result = await session.call_tool("coles_search", {"query": "milk"})
            products = result[0].content.get('items', [])
            total = result[0].content.get('total', 0)
            demo_mode = result[0].content.get('demo_mode', False)

            print(f"Query: 'milk'")
            print(f"Total found: {total}")
            print(f"Demo mode: {demo_mode}")
            print(f"Products returned: {len(products)}")
            if products:
                print("\nFirst 3 products:")
                for i, product in enumerate(products[:3], 1):
                    name = product.get('name', 'Unknown')
                    price = product.get('price', 0)
                    print(f"  {i}. {name} - ${price}")
            print()

            # Example 3: Get product details
            if products:
                product_id = products[0].get('id')
                print(f"3. Product Detail (ID: {product_id})")
                print("-" * 40)
                result = await session.call_tool("coles_product_detail", {"product_id": product_id})
                detail = result[0].content
                print(f"Name: {detail.get('name', 'Unknown')}")
                print(f"Price: ${detail.get('price', 0)}")
                print(f"Brand: {detail.get('brand', 'Unknown')}")
                print(f"In Stock: {detail.get('inStock', True)}")
                print()

            # Example 4: Browse specials
            print("4. Weekly Specials")
            print("-" * 40)
            result = await session.call_tool("coles_specials", {})
            specials = result[0].content.get('items', [])
            print(f"Specials available: {len(specials)}")
            if specials:
                print("\nSpecials:")
                for i, special in enumerate(specials[:3], 1):
                    name = special.get('name', 'Unknown')
                    price = special.get('price', 0)
                    print(f"  {i}. {name} - ${price}")
            print()

            # Example 5: View cart
            print("5. View Cart")
            print("-" * 40)
            result = await session.call_tool("coles_view_cart", {})
            cart = result[0].content
            print(f"Cart total: ${cart.get('total', 0)}")
            print(f"Items in cart: {cart.get('item_count', 0)}")
            print(f"Demo mode: {cart.get('demo_mode', False)}")
            print()

            print("=" * 60)
            print("Examples completed successfully!")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
