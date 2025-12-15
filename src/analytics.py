"""
Core analytics engine for market basket analysis.

Key data structures:
- CountsCache: Stores precomputed item support and co-occurrence counts (pairs, trios)
  * item_support: Counter[str] → O(1) lookups for item frequency
  * pair_counts: Counter[frozenset[str]] → frozenset ensures {A,B} == {B,A} (no duplicates)
  * trio_counts: Counter[frozenset[str]] → same deduplication for 3-item bundles
  
Cache-first design:
- Single O(n·b²) pass to build cache from transactions
- All queries then run in O(1) to O(m) time (m = pairs)
- Trades one-time preprocessing cost for fast, repeated queries

Key insight: frozenset prevents storing both {A,B} and {B,A} as separate entries,
reducing memory by ~50% and ensuring consistent pair counting.
"""
from __future__ import annotations
from typing import Dict, Iterable, List, Optional, Tuple
from collections import Counter
from itertools import combinations
import pandas as pd

# -----------------------------
# Cache building
# -----------------------------

class CountsCache:
    """
    Reusable cache of item support and co-occurrence counts.
    
    Design rationale:
    - Store counts once, query many times (amortizes preprocessing cost)
    - Use Counter (hash-based dict) for O(1) average-case lookups
    - Use frozenset keys for undirected pairs/trios (prevents duplicates)
    - Store transaction count (n_tx) to avoid recalculation in metrics
    """
    def __init__(self):
        self.n_tx: int = 0
        self.item_support: Counter[str] = Counter()
        self.pair_counts: Counter[frozenset[str]] = Counter()
        self.trio_counts: Counter[frozenset[str]] = Counter()

def _dedupe_keep_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def build_counts_cache(transactions: List[List[str]], max_k: int = 3) -> CountsCache:
    """
    Build a precomputed cache of item support and co-occurrence counts.
    
    Complexity: O(n·b²) where n = transactions, b = average basket size
    - n iterations (one per transaction)
    - per transaction: ~b² pairs (C(b,2) = b*(b-1)/2) via combinations()
    - typical: n=15K, b=2.54 → ~45M operations, ~100ms
    
    Algorithm:
    1. Deduplicate items in basket (preserve order, avoid double-counting)
    2. Use itertools.combinations() to generate all pairs and trios exhaustively
    3. Store as frozenset in Counter to avoid {A,B} vs {B,A} duplicates
    4. Skip trios if max_k < 3 (trades speed for optional features)
    
    Note: Deduplication prevents inflated co-occurrence counts from duplicate items
    in a single transaction (e.g., buying the same item twice on one visit).
    """
    cache = CountsCache()
    cache.n_tx = len(transactions)

    for basket in transactions:
        uniq = _dedupe_keep_order(basket)
        # item support
        cache.item_support.update(uniq)
        # pairs
        for a, b in combinations(uniq, 2):
            cache.pair_counts[frozenset((a, b))] += 1
        # trios
        if max_k >= 3 and len(uniq) >= 3:
            for trio in combinations(uniq, 3):
                cache.trio_counts[frozenset(trio)] += 1

    return cache

# -----------------------------
# Queries
# -----------------------------

def top_copurchases_for_item(
    item: str,
    cache: CountsCache,
    top_k: int = 10,
    min_count: int = 1
) -> List[Tuple[str, int]]:
    """
    Find top-K items most frequently co-purchased with a given item.
    
    Complexity: O(m + k·log(k)) where m = number of pairs
    - O(m) to iterate all pairs and filter for target item
    - O(k·log k) to sort (typically k=10, negligible)
    - Most dataset: m ~ 1% of i² (i=items), so very selective
    
    Returns: List of (other_item, co_purchase_count) tuples sorted by count descending
    
    Example: top_copurchases_for_item("milk", cache) → [("bread", 450), ("butter", 320), ...]
    """
    neighbors: List[Tuple[str, int]] = []
    for p, c in cache.pair_counts.items():
        if item in p and c >= min_count:
            other = next(iter(p - {item}))
            neighbors.append((other, c))
    neighbors.sort(key=lambda x: (-x[1], x[0]))
    return neighbors[:top_k]

def top_bundles(
    cache: CountsCache,
    top_n: int = 3,
    include_trios: bool = True
) -> List[Tuple[Tuple[str, ...], int]]:
    """
    Return the top-N bundles (pairs and optionally trios), sorted by count desc.
    Each bundle is returned as (items_tuple_sorted, count).
    """
    entries: List[Tuple[Tuple[str, ...], int]] = []
    for p, c in cache.pair_counts.items():
        entries.append((tuple(sorted(p)), c))
    if include_trios:
        for t, c in cache.trio_counts.items():
            entries.append((tuple(sorted(t)), c))
    entries.sort(key=lambda x: (-x[1], x[0]))
    return entries[:top_n]

def pair_check_simple(
    a: str,
    b: str,
    cache: CountsCache,
    min_count: int = 5,
    min_support: float = 0.01
) -> dict:
    """
    Fast O(1) pair check for quick YES/NO decision on co-purchase strength.
    
    Returns only essentials:
    - count: absolute co-purchase frequency
    - support: count / total_transactions (market penetration)
    - n: total transactions (for reference)
    - often: bool (count >= threshold AND support >= threshold)
    
    Use case: "Do customers often buy A and B together?"
    Answer: Binary YES/NO based on thresholds.
    
    For detailed analysis (confidence, lift), use pair_stats() instead.
    """
    n = cache.n_tx
    count = int(cache.pair_counts.get(frozenset((a, b)), 0))
    support = (count / n) if n > 0 else 0.0
    return {
        "count": count,
        "support": support,
        "n": n,
        "often": (count >= min_count) and (support >= min_support),
    }

def pair_stats(
    a: str,
    b: str,
    cache: CountsCache,
    min_count: int = 5,
    min_support: float = 0.01
) -> Dict[str, float | int | bool]:
    """
    Comprehensive O(1) pair analysis with business metrics.
    
    Returns:
    - count_ab, support_ab: absolute and relative co-purchase frequency
    - support_a, support_b: individual item popularity
    - confidence_a_to_b: P(B|A) = likelihood of B given A purchased (buyer targeting)
    - confidence_b_to_a: P(A|B) = likelihood of A given B purchased (complementary insight)
    - lift: support(A,B) / [support(A) * support(B)]
      * lift > 1.0 = positive association (buy together more than random)
      * lift = 1.0 = independence
      * lift < 1.0 = negative association (substitute goods)
    - often: bool threshold-based decision
    
    Business use: Identify cross-selling opportunities and bundle pricing.
    """
    n = cache.n_tx
    count_ab = int(cache.pair_counts.get(frozenset((a, b)), 0))
    support_ab = (count_ab / n) if n > 0 else 0.0

    count_a = int(cache.item_support.get(a, 0))
    count_b = int(cache.item_support.get(b, 0))
    support_a = (count_a / n) if n > 0 else 0.0
    support_b = (count_b / n) if n > 0 else 0.0

    confidence_a_to_b = (count_ab / count_a) if count_a > 0 else 0.0
    confidence_b_to_a = (count_ab / count_b) if count_b > 0 else 0.0
    lift = (support_ab / (support_a * support_b)) if (support_a > 0 and support_b > 0) else 0.0

    return {
        "count_ab": count_ab,
        "support_ab": support_ab,
        "support_a": support_a,
        "support_b": support_b,
        "confidence_a_to_b": confidence_a_to_b,
        "confidence_b_to_a": confidence_b_to_a,
        "lift": lift,
        "often": (count_ab >= min_count) and (support_ab >= min_support),
    }

def cooccurrence_matrix(
    cache: CountsCache,
    items_subset: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Build a symmetric co-occurrence matrix (i × i DataFrame of pair counts).
    
    Complexity: O(i² + m) where i = items selected, m = pairs
    - O(i²) to initialize DataFrame
    - O(m) to fill in pair counts from cache
    - Critical: matrix is dense (all i² cells created), so only use for small subsets
    
    Design:
    - rows & columns are item names (sorted for consistency)
    - df[a][b] = co-occurrence count for pair (a, b)
    - matrix is symmetric (df[a][b] = df[b][a])
    - diagonal df[a][a] = item support (single-item frequency)
    
    Warning: For i=1000, matrix has 1M cells; for i=10K, 100M cells (prohibitive).
    Always use items_subset for real datasets or consider sparse formats (scipy.sparse).
    
    Returns: Pandas DataFrame ready for heatmap visualization
    """
    # choose items
    if items_subset is None:
        items = list(cache.item_support.keys())
    else:
        items = list(items_subset)
    items_sorted = sorted(items)
    # init DataFrame
    df = pd.DataFrame(0, index=items_sorted, columns=items_sorted, dtype=int)
    # fill pairs
    for p, c in cache.pair_counts.items():
        a, b = tuple(p)
        if a in df.index and b in df.columns:
            df.at[a, b] = c
            df.at[b, a] = c
    # diagonal can show single-item support (optional)
    for i in items_sorted:
        df.at[i, i] = int(cache.item_support.get(i, 0))
    return df


