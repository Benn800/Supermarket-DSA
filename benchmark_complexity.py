"""
Benchmark script to empirically validate computational complexity claims.

Purpose:
- Measure actual execution times vs. theoretical complexity predictions
- Validate that O(n), O(1), O(i²) scaling holds in practice
- Correct numerical estimates (e.g., cache build time, matrix generation)
- Generate plots showing empirical complexity curves

Key insight:
- Theory predicts complexity class (O(n), O(n²), etc.)
- Empirical timing confirms if implementation matches theory

Usage:
    python benchmark_complexity.py
    
Output:
    - Console: summary table with size ratios, time ratios, complexity classification
    - output/complexity_plots.png: visual plots of all 5 benchmarks
"""
from __future__ import annotations
import time
import random
from typing import List, Callable
from collections import Counter
from itertools import combinations
import matplotlib.pyplot as plt
from pathlib import Path

from src.analytics import (
    build_counts_cache,
    top_copurchases_for_item,
    pair_check_simple,
    cooccurrence_matrix,
    top_bundles
)

# ====================================
# Synthetic Data Generation
# ====================================

def generate_transactions(n_transactions: int, n_items: int = 167, avg_basket_size: int = 3) -> List[List[str]]:
    """
    Generate synthetic transaction data matching real supermarket dataset characteristics.
    
    Real dataset stats:
    - Transactions: 14,963
    - Unique items: 167
    - Avg basket size: 2.54
    - Max basket size: 10
    """
    items = [f"item_{i}" for i in range(n_items)]
    transactions = []
    for _ in range(n_transactions):
        basket_size = max(1, min(10, int(random.gauss(avg_basket_size, 1.5))))
        basket = random.sample(items, min(basket_size, n_items))
        transactions.append(basket)
    return transactions

# ====================================
# Timing Utilities
# ====================================

def time_function(func: Callable, *args, **kwargs) -> tuple[float, any]:
    """Time a function and return (elapsed_time, result)."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return elapsed, result

def measure_scaling(
    func: Callable,
    sizes: List[int],
    setup_func: Callable,
    label: str
) -> dict:
    """
    Measure how execution time scales with input size.
    
    Args:
        func: Function to benchmark
        sizes: List of input sizes to test
        setup_func: Function that takes size and returns args for func
        label: Description for printing
    
    Returns:
        Dictionary with sizes and timings
    """
    print(f"\n{'='*60}")
    print(f"Benchmarking: {label}")
    print(f"{'='*60}")
    
    timings = []
    for size in sizes:
        args = setup_func(size)
        elapsed, _ = time_function(func, *args)
        timings.append(elapsed)
        print(f"  n={size:7,} → {elapsed:8.5f}s  ({elapsed*1000:8.2f}ms)")
    
    return {"sizes": sizes, "timings": timings, "label": label}

# ====================================
# Benchmark 1: build_counts_cache - O(n·b²)
# ====================================

def bench_build_cache():
    """Measure cache building complexity: O(n·b²)"""
    
    # Test varying number of transactions (n) - matching real dataset scale
    sizes_n = [1000, 5000, 10000, 15000, 20000, 30000]
    
    def setup_varying_n(n):
        txs = generate_transactions(n, n_items=167, avg_basket_size=3)
        return (txs, 3)  # max_k=3
    
    result_n = measure_scaling(
        build_counts_cache,
        sizes_n,
        setup_varying_n,
        "build_counts_cache - varying n (transactions)"
    )
    
    # Test varying basket size (b) - matching real range
    sizes_b = [2, 3, 4, 5, 7, 10]
    
    def setup_varying_b(b):
        txs = generate_transactions(5000, n_items=167, avg_basket_size=b)
        return (txs, 3)
    
    result_b = measure_scaling(
        build_counts_cache,
        sizes_b,
        setup_varying_b,
        "build_counts_cache - varying b (basket size)"
    )
    
    return [result_n, result_b]

# ====================================
# Benchmark 2: top_copurchases_for_item - O(m)
# ====================================

def bench_top_copurchases():
    """Measure top_copurchases complexity: O(m) where m = pairs"""
    
    sizes = [1000, 5000, 10000, 15000, 20000]
    
    def setup(n):
        txs = generate_transactions(n, n_items=167, avg_basket_size=3)
        cache = build_counts_cache(txs, max_k=2)
        # Pick a common item
        most_common = cache.item_support.most_common(1)[0][0]
        return (most_common, cache, 10)
    
    result = measure_scaling(
        top_copurchases_for_item,
        sizes,
        setup,
        "top_copurchases_for_item - varying m (pairs)"
    )
    
    return [result]

# ====================================
# Benchmark 3: pair_check_simple - O(1)
# ====================================

def bench_pair_check():
    """Measure pair_check complexity: O(1) - constant time"""
    
    sizes = [1000, 5000, 10000, 15000, 20000, 30000]
    
    def setup(n):
        txs = generate_transactions(n, n_items=167, avg_basket_size=3)
        cache = build_counts_cache(txs, max_k=2)
        # Pick two common items
        top_items = [item for item, _ in cache.item_support.most_common(2)]
        return (top_items[0], top_items[1], cache)
    
    result = measure_scaling(
        pair_check_simple,
        sizes,
        setup,
        "pair_check_simple - O(1) verification"
    )
    
    return [result]

# ====================================
# Benchmark 4: cooccurrence_matrix - O(i²)
# ====================================

def bench_cooccurrence_matrix():
    """Measure matrix building: O(i²) where i = matrix size"""
    
    sizes = [20, 50, 75, 100, 125, 167]
    
    def setup(i):
        txs = generate_transactions(5000, n_items=i, avg_basket_size=3)
        cache = build_counts_cache(txs, max_k=2)
        # Use all items for matrix
        return (cache, None)
    
    result = measure_scaling(
        cooccurrence_matrix,
        sizes,
        setup,
        "cooccurrence_matrix - varying i (matrix size)"
    )
    
    return [result]

# ====================================
# Visualization
# ====================================

def plot_results(all_results: List[dict], output_path: str = "output/complexity_plots.png"):
    """Generate plots showing empirical complexity."""
    
    n_plots = len(all_results)
    fig, axes = plt.subplots(3, 2, figsize=(14, 14))
    axes = axes.flatten()
    
    for idx, result in enumerate(all_results):  # Plot all results
        ax = axes[idx]
        sizes = result["sizes"]
        timings = result["timings"]
        
        ax.plot(sizes, timings, 'o-', linewidth=2, markersize=6, color='#2E86AB')
        ax.set_xlabel("Input Size", fontsize=11)
        ax.set_ylabel("Time (seconds)", fontsize=11)
        ax.set_title(result["label"], fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # For O(1) operations, fix y-axis to show flatness
        if "O(1)" in result["label"] or max(timings) < 0.0001:
            avg_time = sum(timings) / len(timings)
            ax.set_ylim([0, avg_time * 3])  # Show range to emphasize flatness
        
        # Add trend annotation
        if len(timings) > 1:
            ratio = timings[-1] / timings[0]
            size_ratio = sizes[-1] / sizes[0]
            ax.text(0.05, 0.95, 
                   f"Size ×{size_ratio:.1f} → Time ×{ratio:.1f}",
                   transform=ax.transAxes,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Remove unused subplots
    for idx in range(len(all_results), 6):
        fig.delaxes(axes[idx])
    
    plt.tight_layout()
    Path("output").mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\n✓ Plots saved to: {output_path}")

# ====================================
# Summary Statistics
# ====================================

def print_summary(all_results: List[dict]):
    """Print summary table of results."""
    print("\n" + "="*80)
    print("COMPLEXITY SUMMARY")
    print("="*80)
    
    for result in all_results:
        sizes = result["sizes"]
        timings = result["timings"]
        
        if len(timings) < 2:
            continue
        
        # Calculate growth rate
        size_ratio = sizes[-1] / sizes[0]
        time_ratio = timings[-1] / timings[0]
        
        # Expected ratios for different complexities
        expected_O1 = 1.0
        expected_On = size_ratio
        expected_On2 = size_ratio ** 2
        expected_Onlogn = size_ratio * (sizes[-1] / sizes[0])
        
        print(f"\n{result['label']}")
        print(f"  Input size:    {sizes[0]:,} → {sizes[-1]:,} (×{size_ratio:.1f})")
        print(f"  Time:          {timings[0]:.5f}s → {timings[-1]:.5f}s (×{time_ratio:.1f})")
        print(f"  Expected for:")
        print(f"    O(1):        ×{expected_O1:.1f}")
        print(f"    O(n):        ×{expected_On:.1f}")
        print(f"    O(n²):       ×{expected_On2:.1f}")
        
        # Determine best fit
        if abs(time_ratio - expected_O1) < 2:
            best_fit = "O(1) - Constant"
        elif abs(time_ratio - expected_On) < expected_On * 0.5:
            best_fit = "O(n) - Linear"
        elif abs(time_ratio - expected_On2) < expected_On2 * 0.5:
            best_fit = "O(n²) - Quadratic"
        else:
            best_fit = f"~O(n^{(time_ratio / expected_On):.2f})"
        
        print(f"  → Best fit:    {best_fit}")

# ====================================
# Main Execution
# ====================================

def main():
    """Run all benchmarks and generate report."""
    print("COMPUTATIONAL COMPLEXITY BENCHMARKING")
    print("=" * 80)
    print("This script measures actual execution times to validate theoretical")
    print("=" * 80)
    
    random.seed(42)  # Reproducibility
    
    all_results = []
    
    # Run benchmarks
    all_results.extend(bench_build_cache())
    all_results.extend(bench_top_copurchases())
    all_results.extend(bench_pair_check())
    all_results.extend(bench_cooccurrence_matrix())
    
    # Generate summary
    print_summary(all_results)
    
    # Plot results
    plot_results(all_results)
    
    print("\n" + "="*80)
    print("✓ Benchmarking complete!")
    print("="*80)

if __name__ == "__main__":
    main()
