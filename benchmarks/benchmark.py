# benchmark_compress_text.py

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from compressor import compress_text
import time
import random
import string
import json
import os


def generate_test_input(size, pattern_type="random"):
    """Generate test strings of various sizes and patterns."""
    if pattern_type == "random":
        return ''.join(random.choice(string.ascii_lowercase) for _ in range(size))

    elif pattern_type == "repeated_pairs":
        return ("ab" * (size // 2))[:size]

    elif pattern_type == "uniform":
        return "a" * size

    elif pattern_type == "mixed_patterns":
        # Mix of repeated patterns and random
        result = []
        chunk_size = 100
        for i in range(0, size, chunk_size):
            if i % 400 == 0:
                result.append("ab" * (chunk_size // 2))
            elif i % 400 == 100:
                result.append("a" * chunk_size)
            elif i % 400 == 200:
                result.append(''.join(random.choice(string.ascii_lowercase)
                                      for _ in range(chunk_size)))
            else:
                result.append("xyz" * (chunk_size // 3))

        full_text = ''.join(result)
        return full_text[:size]

    else:
        raise ValueError(f"Unknown pattern type: {pattern_type}")


def benchmark_single(size, k, pattern_type="random"):
    """Run a single benchmark and return (time_seconds, output_length)."""
    text = generate_test_input(size, pattern_type)

    start = time.time()
    result = compress_text(text, k)
    elapsed = time.time() - start

    return elapsed, len(result)


def run_linear_scalability_tests(results_store):
    """
    Cases 9-14: Linear Scalability (10k → 90k chars).
    Verifies naive solutions start slowing down here.
    """
    print("\n" + "=" * 100)
    print("LINEAR SCALABILITY TESTS (Cases 9-14: 10k → 90k chars)")
    print("=" * 100)

    sizes_linear = [10_000, 30_000, 50_000, 70_000, 90_000]
    patterns = ["random", "repeated_pairs", "uniform", "mixed_patterns"]
    k = 10  # moderate K value

    results_store["linear"] = []

    for pattern in patterns:
        print(f"\n--- Pattern: {pattern.upper()} ---")
        print(f"{'Size':>12} | {'K':>2} | {'Time (ms)':>12} | {'Result Len':>12} | {'Compression %':>14}")
        print("-" * 70)

        for size in sizes_linear:
            elapsed, result_len = benchmark_single(size, k, pattern_type=pattern)
            compression_pct = (result_len / size) * 100

            print(f"{size:>12,} | {k:>2} | {elapsed*1000:>12.2f} | "
                  f"{result_len:>12,} | {compression_pct:>13.1f}%")

            results_store["linear"].append({
                "pattern": pattern,
                "size": size,
                "k": k,
                "time_seconds": elapsed,
                "result_length": result_len,
                "compression_percent": compression_pct,
            })

    print("\n✓ Linear scalability tests complete")


def run_stress_tests(results_store):
    """
    Cases 15-20: Stress Tests (100k → 1M chars).
    Designed to trigger Time Limit Exceeded (TLE) or Memory Limit Exceeded (MLE)
    on inefficient solutions.
    """
    print("\n" + "=" * 100)
    print("STRESS TESTS (Cases 15-20: 100k → 1M chars)")
    print("=" * 100)

    sizes_stress = [100_000, 200_000, 500_000, 1_000_000]
    patterns = ["random", "repeated_pairs", "uniform", "mixed_patterns"]
    ks = [5, 10, 26]  # small, moderate, and worst-case

    results_store["stress"] = []

    total_stress_tests = 0
    tle_warnings = 0

    for pattern in patterns:
        print(f"\n=== Pattern: {pattern.upper()} ===")

        for size in sizes_stress:
            print(f"\n  Size {size:>10,} chars:")
            print(f"  {'K':>3} | {'Time (s)':>10} | {'Result Len':>12} | {'Compression %':>14} | Status")
            print("  " + "-" * 70)

            for k in ks:
                try:
                    elapsed, result_len = benchmark_single(size, k, pattern_type=pattern)
                    compression_pct = (result_len / size) * 100

                    status = "PASS"
                    if elapsed > 3.0:
                        status = "TLE>3s"
                        tle_warnings += 1
                    elif elapsed > 2.5:
                        status = "WARN>2.5s"
                        tle_warnings += 1

                    print(f"  {k:>3} | {elapsed:>10.3f} | {result_len:>12,} | "
                          f"{compression_pct:>13.1f}% | {status}")

                    results_store["stress"].append({
                        "pattern": pattern,
                        "size": size,
                        "k": k,
                        "time_seconds": elapsed,
                        "result_length": result_len,
                        "compression_percent": compression_pct,
                        "status": status,
                    })

                    total_stress_tests += 1

                except Exception as e:
                    err_str = str(e)
                    print(f"  {k:>3} | {'ERROR':>10} | {'N/A':>12} | {'N/A':>13} | {err_str[:30]}")
                    results_store["stress"].append({
                        "pattern": pattern,
                        "size": size,
                        "k": k,
                        "time_seconds": None,
                        "result_length": None,
                        "compression_percent": None,
                        "status": f"ERROR: {err_str}",
                    })

    print(f"\n✓ Stress tests complete (Total: {total_stress_tests} tests run)")
    if tle_warnings > 0:
        print(f"  ⚠️  {tle_warnings} tests with time warnings (consider optimization)")


def run_edge_case_stress(results_store):
    """
    Additional stress tests on specific patterns known to be problematic.
    """
    print("\n" + "=" * 100)
    print("ADDITIONAL EDGE CASE STRESS TESTS")
    print("=" * 100)

    results_store["edge_stress"] = []

    tests = [
        ("uniform",        300_000, 26, "Very large uniform string (a*300k, K=26)"),
        ("repeated_pairs", 250_000, 26, "Highly compressible repeated pattern (ab*250k, K=26)"),
        ("random",         500_000, 20, "Large random string (500k, K=20)"),
        ("mixed_patterns", 750_000, 26, "Mixed patterns (750k, K=26)"),
    ]

    for pattern, size, k, description in tests:
        print(f"\n{description}")
        elapsed, result_len = benchmark_single(size, k, pattern_type=pattern)
        status = "PASS" if elapsed < 3.0 else "TLE>3s"
        print(f"  Time: {elapsed:.3f}s | Result: {result_len:,} chars | Status: {status}")

        results_store["edge_stress"].append({
            "description": description,
            "pattern": pattern,
            "size": size,
            "k": k,
            "time_seconds": elapsed,
            "result_length": result_len,
            "compression_percent": (result_len / size) * 100,
            "status": status,
        })


def write_results_to_json(results_store, filename="benchmark_results.json"):
    """Write the results dictionary to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results_store, f, indent=2)
    print(f"\n📁 Benchmark results written to {os.path.abspath(filename)}")


def main():
    random.seed(42)  # Reproducibility

    results = {
        "linear": [],
        "stress": [],
        "edge_stress": [],
        "meta": {
            "description": "compress_text benchmark results for Assignment 1",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }

    print("\n" + "=" * 100)
    print("COMPREHENSIVE BENCHMARK SUITE FOR compress_text")
    print("Aligned with grading categories: Cases 9–20")
    print("=" * 100)

    run_linear_scalability_tests(results)
    run_stress_tests(results)
    run_edge_case_stress(results)
    write_results_to_json(results)

    print("\n" + "=" * 100)
    print("ALL BENCHMARKS COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()
