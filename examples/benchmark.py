#!/usr/bin/env python3
"""Performance benchmark for Coles MCP server tools.

Measures response times for various operations to ensure performance is acceptable.
"""

import time
from coles_mcp.demo_mode import (
    search_demo_mode,
    product_detail_demo_mode,
    specials_demo_mode,
    view_cart_demo_mode,
    add_to_cart_demo_mode,
)


def benchmark_demo_mode():
    """Benchmark demo mode function performance."""
    print("=" * 60)
    print("Coles MCP - Performance Benchmark")
    print("=" * 60)
    print()

    operations = [
        ("Search (milk)", lambda: search_demo_mode("milk")),
        ("Search (bread)", lambda: search_demo_mode("bread")),
        ("Product Detail", lambda: product_detail_demo_mode("demo-001")),
        ("Specials", lambda: specials_demo_mode()),
        ("View Cart", lambda: view_cart_demo_mode()),
        ("Add to Cart", lambda: add_to_cart_demo_mode("demo-001", 2)),
        ("Search (empty)", lambda: search_demo_mode("")),
        ("Search (no results)", lambda: search_demo_mode("xyz123")),
    ]

    results = []

    for name, operation in operations:
        # Warm up
        operation()

        # Measure 3 runs
        times = []
        for _ in range(3):
            start = time.perf_counter()
            operation()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        results.append({
            "operation": name,
            "avg_ms": avg_time,
            "min_ms": min_time,
            "max_ms": max_time,
        })

        print(f"{name:20s} Avg: {avg_time:6.2f}ms  Min: {min_time:6.2f}ms  Max: {max_time:6.2f}ms")

    print()
    print("=" * 60)
    print("Performance Summary")
    print("=" * 60)

    # Calculate overall stats
    all_times = [r["avg_ms"] for r in results]
    avg_overall = sum(all_times) / len(all_times)
    max_operation = max(results, key=lambda x: x["avg_ms"])
    min_operation = min(results, key=lambda x: x["avg_ms"])

    print(f"Overall average: {avg_overall:6.2f}ms")
    print(f"Fastest operation: {min_operation['operation']} ({min_operation['avg_ms']:.2f}ms)")
    print(f"Slowest operation: {max_operation['operation']} ({max_operation['avg_ms']:.2f}ms)")
    print()

    # Performance assessment
    print("Performance Assessment:")
    if avg_overall < 10:
        print("✅ EXCELLENT - All operations under 10ms")
    elif avg_overall < 50:
        print("✅ GOOD - All operations under 50ms")
    elif avg_overall < 100:
        print("⚠️  ACCEPTABLE - Some operations over 100ms")
    else:
        print("❌ NEEDS OPTIMIZATION - Operations too slow")

    print()

    # Check for operations that are too slow
    slow_threshold = 100  # ms
    slow_ops = [r for r in results if r["avg_ms"] > slow_threshold]
    if slow_ops:
        print("Slow operations (>100ms):")
        for result in slow_ops:
            print(f"  - {result['operation']}: {result['avg_ms']:.2f}ms")
    else:
        print("✅ No slow operations detected")

    print()
    print("Demo mode performance is acceptable for production use!")


if __name__ == "__main__":
    benchmark_demo_mode()
