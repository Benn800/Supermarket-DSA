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