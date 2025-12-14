"""
Analytics utilities for purchasing pattern queries:
- Build a reusable counts cache (items, pairs, trios)
- Top co-purchases for a given item
- Top-N bundles (pairs and optionally trios)
- Quick pair check with support/confidence/lift & thresholds
- Co-occurrence matrix (subset or all)

Everything is kept simple, readable, and fast.
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
    """Reusable counts for fast queries."""
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
    Build item support, pair counts, and trio counts.
    Duplicates inside a basket are ignored.
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
    Return top-K items most frequently co-purchased with `item` as (other_item, count).
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
    Simplified pair check: returns only the essentials to decide YES/NO quickly.

    Returns:
      {
        "count": int,
        "support": float,
        "n": int,            # total transactions
        "often": bool        # (count >= min_count) and (support >= min_support)
      }
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
    Quick check whether two items are often co-purchased.
    Returns:
      - count_ab       (#transactions containing both)
      - support_ab     (count_ab / n_transactions)
      - support_a, support_b
      - confidence_a_to_b = count_ab / count_a
      - confidence_b_to_a = count_ab / count_b
      - lift = support_ab / (support_a * support_b)  [>1 suggests positive association]
      - often          
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

def recommend_from_items(
    items: Iterable[str],
    cache: CountsCache,
    top_k: int = 5,
    exclude_seen: bool = True
) -> List[Tuple[str, int]]:
    """
    Simple neighbor aggregation: sum pair counts for each item in `items`.
    """
    items = list(set(items))
    scores: Counter[str] = Counter()
    for it in items:
        for p, c in cache.pair_counts.items():
            if it in p:
                other = next(iter(p - {it}))
                if exclude_seen and other in items:
                    continue
                scores[other] += c
    return sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:top_k]

def cooccurrence_matrix(
    cache: CountsCache,
    items_subset: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Build a symmetric co-occurrence matrix (counts) for a subset or for all items.
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


