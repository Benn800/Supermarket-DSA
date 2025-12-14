from __future__ import annotations
import argparse
from typing import List
from src.data_loader import TransactionLoader
from src.analytics import (
    build_counts_cache,
    top_copurchases_for_item,
    top_bundles,
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

MENU = """
[1] Top co‑purchases for an item
[2] Top K most common bundles (pairs & trios) 
[3] Check if two items are often co‑purchased
[4] Plot: Top co‑purchases (bar chart)
[5] Plot: Top bundles (bar chart)
[6] Plot: Co‑occurrence heatmap
[7] Plot: Co‑occurrence network (thresholded)
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
            a = input("Item A: ").strip()
            b = input("Item B: ").strip()
            min_count = int(input("Min count (default 5): ") or "5")
            min_support = float(input("Min support (default 0.01): ") or "0.01")
            metrics = pair_stats(a, b, cache=cache, min_count=min_count, min_support=min_support)
            print(f"Count({a},{b}) = {metrics['count_ab']}")
            print(f"Support({a},{b}) = {metrics['support_ab']:.4f}  (n={cache.n_tx})")
            print(f"Support({a}) = {metrics['support_a']:.4f} | Support({b}) = {metrics['support_b']:.4f}")
            print(f"Confidence {a}->{b} = {metrics['confidence_a_to_b']:.4f}")
            print(f"Confidence {b}->{a} = {metrics['confidence_b_to_a']:.4f}")
            print(f"Lift = {metrics['lift']:.4f}")
            print("Often?", "YES" if metrics["often"] else "NO")

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
            m = int(input("Min edge count (default 5): ") or "5")
            subset = input("Subset nodes (comma‑separated, blank for all): ").strip()
            nodes = [s.strip() for s in subset.split(",") if s.strip()] if subset else None
            path = plot_cooccurrence_network(cache, min_count=m, nodes_subset=nodes)
            print(f"Saved: {path}")

        elif choice == "0":
            print("Bye!")
            break

        else:
            print("Invalid option.")

def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Task 2 CLI")
    p.add_argument("csv_path", help="Path to Supermarket_dataset_PAI.csv")
    return p
