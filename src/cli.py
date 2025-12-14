from __future__ import annotations
import argparse
from typing import List
from src.data_loader import TransactionLoader
from src.analytics import (
    build_counts_cache,
    top_copurchases_for_item,
    top_bundles,
    pair_check_simple,
    pair_stats,
    recommend_from_items,
    cooccurrence_matrix,
)
from .visualization import (
    plot_top_copurchases_bar,
    plot_top_bundles_bar,
    plot_cooccurrence_heatmap,
    plot_cooccurrence_network,
)
from src.store_sql import save_counts_to_sql, load_top_pairs_from_sql

def _maybe_get_existing_item(prompt: str, cache) -> str:
    """Ask until user enters a non-empty item; warn if item not in dataset."""
    while True:
        item = input(prompt).strip()
        if not item:
            print("Please enter a non-empty item name.")
            continue
        if item not in cache.item_support:
            print(f'Warning: "{item}" not found (case-sensitive).')
            if input("Continue anyway? (y/N): ").strip().lower() != "y":
                continue
        return item

def _ask_int(prompt: str, default: int) -> int:
    raw = input(prompt).strip()
    if not raw: return default
    try:
        return int(raw)
    except ValueError:
        print("Please enter a valid integer.")
        return _ask_int(prompt, default)

def _ask_float(prompt: str, default: float) -> float:
    raw = input(prompt).strip()
    if not raw: return default
    try:
        return float(raw)
    except ValueError:
        print("Please enter a valid number (float).")
        return _ask_float(prompt, default)

MENU = """
[1] Top co‑purchases for an item
[2] Top K most common bundles (pairs & trios) 
[3] Check if two items are often co‑purchased
[4] Plot: Top co‑purchases (bar chart)
[5] Plot: Top bundles (bar chart)
[6] Plot: Co‑occurrence heatmap
[7] Plot: Co‑occurrence network (thresholded)
[8] Save counts to SQLite (LO3)
[9] Load top pairs from SQLite
[0] Exit
"""

def run_cli(csv_path: str) -> None:
    print("Loading transactions...")
    tl = TransactionLoader(csv_path)
    transactions: List[List[str]] = tl.load_transactions()
    print(f"Transactions loaded: {len(transactions)}")

    print("Building counts cache...")
    cache = build_counts_cache(transactions, max_k=3)
    print("Ready.")

    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()

        if choice == "1":
            item = input("Item name: ").strip()
            k = int(input("Top K (default 10): ") or "10")
            results = top_copurchases_for_item(item, cache=cache, top_k=k, min_count=1)
            if not results:
                print(f'No co‑purchases found for "{item}".')
            else:
                for other, c in results:
                    print(f"{item} — {other}: {c}")

        elif choice == "2":
            k = int(input("Top K bundles (default 3): ") or "3")
            include_trios_str = input("Include trios? (y/N): ").strip().lower()
            include_trios = include_trios_str == "y"
            top = top_bundles(cache=cache, top_n=k, include_trios=include_trios)
            if not top:
                print("No bundles found.")
            else:
                for items, cnt in top:
                    print(f"{' + '.join(items)} | count={cnt}")

        elif choice == "3":
            # Simplified pair check: just count, support, YES/NO
            a = _maybe_get_existing_item("Item A: ", cache)
            b = _maybe_get_existing_item("Item B: ", cache)
            min_count   = _ask_int("Min count (default 5): ", 5)
            min_support = _ask_float("Min support (default 0.01): ", 0.01)

            result = pair_check_simple(a, b, cache=cache, min_count=min_count, min_support=min_support)
            print(f"Count({a},{b})   = {result['count']}")
            print(f"Support({a},{b}) = {result['support']:.4f}  (n={result['n']})")
            print("Often?            ", "YES" if result["often"] else "NO")

            # Optional: let user expand to verbose metrics if needed
            if input("Show detailed metrics (confidence/lift)? (y/N): ").strip().lower() == "y":
                metrics = pair_stats(a, b, cache=cache, min_count=min_count, min_support=min_support)
                print(f"Confidence {a}->{b} = {metrics['confidence_a_to_b']:.4f}")
                print(f"Confidence {b}->{a} = {metrics['confidence_b_to_a']:.4f}")
                print(f"Lift                 = {metrics['lift']:.4f}")

        elif choice == "4":
            item = input("Item name: ").strip()
            k = int(input("Top K (default 10): ") or "10")
            pairs = top_copurchases_for_item(item, cache=cache, top_k=k, min_count=1)
            path = plot_top_copurchases_bar(item, pairs)
            print(f"Saved: {path}")

        elif choice == "5":
            top = top_bundles(cache=cache, top_n=10, include_trios=True)
            path = plot_top_bundles_bar(top, title="Top bundles")
            print(f"Saved: {path}")

        elif choice == "6":
            subset = input("Subset items (comma‑separated, blank for all): ").strip()
            items = [s.strip() for s in subset.split(",") if s.strip()] if subset else None
            df = cooccurrence_matrix(cache, items_subset=items)
            path = plot_cooccurrence_heatmap(df, title="Co-occurrence matrix")
            print(f"Saved: {path}")

        elif choice == "7":
            m = int(input("Min edge count (default 50): ") or "50")
            l = float(input("Min lift (default 1.05): ") or "1.05")
            subset = input("Subset nodes (comma‑separated, blank for all): ").strip()
            nodes = [s.strip() for s in subset.split(",") if s.strip()] if subset else None
            path = plot_cooccurrence_network(
                            cache, min_count=m, min_lift=l, nodes_subset=nodes,
                            title=f"Co-occurrence (count≥{m}, lift≥{l})"
                            )
            print(f"Saved: {path}")
        
        elif choice == "8":
            db = input("DB path (default output/pai_counts.db): ").strip() or "output/pai_counts.db"
            try:
                save_counts_to_sql(cache, db_path=db)
                print(f"Saved item_support and pair_counts to {db}")
            except Exception as e:
                print(f"Save error: {e}")

        elif choice == "9":
            db = input("DB path (default output/pai_counts.db): ").strip() or "output/pai_counts.db"
            k  = int(input("Top K (default 10): ").strip() or "10")
            try:
                rows = load_top_pairs_from_sql(db_path=db, k=k)
                if not rows:
                    print("No rows found. Did you run [8] to save first?")
                else:
                    for a, b, cnt in rows:
                        print(f"{a} + {b} | count={cnt}")
            except Exception as e:
                print(f"Load error: {e}")

        elif choice == "0":
            print("Bye!")
            break

        else:
            print("Invalid option.")

def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Task 2 CLI")
    p.add_argument("csv_path", help="Path to Supermarket_dataset_PAI.csv")
    return p
