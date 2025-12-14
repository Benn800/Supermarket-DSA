
"""
Plotting helpers: bar charts, heatmap, and co-occurrence network.
"""
from __future__ import annotations
from typing import List, Tuple, Optional
from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from src.analytics import CountsCache

def plot_top_copurchases_bar(
    item: str,
    top_pairs: List[Tuple[str, int]],
    output_path: str = "output/top_copurchases_bar.png"
) -> str:
    labels = [x for x, _ in top_pairs]
    counts = [c for _, c in top_pairs]
    plt.figure(figsize=(10, 6))
    plt.bar(labels, counts, color="#4C72B0")
    plt.title(f"Top co-purchases with {item}")
    plt.xlabel("Item")
    plt.ylabel("Co-purchase count")
    plt.xticks(rotation=45, ha="right")
    Path("output").mkdir(exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path

def plot_top_bundles_bar(
    bundles: List[Tuple[Tuple[str, ...], int]],
    title: str = "Top bundles",
    output_path: str = "output/top_bundles_bar.png"
) -> str:
    labels = [" + ".join(b) for b, _ in bundles]
    counts = [c for _, c in bundles]
    plt.figure(figsize=(10, 6))
    plt.bar(labels, counts, color="#55A868")
    plt.title(title)
    plt.xlabel("Bundle (items)")
    plt.ylabel("Count")
    plt.xticks(rotation=45, ha="right")
    Path("output").mkdir(exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path

def plot_cooccurrence_heatmap(
    df: pd.DataFrame,
    title: str = "Co-occurrence matrix",
    output_path: str = "output/cooccurrence_heatmap.png"
) -> str:
    plt.figure(figsize=(10, 8))
    plt.imshow(df.values, cmap="Blues")
    plt.colorbar()
    plt.xticks(range(len(df.columns)), list(df.columns), rotation=90)
    plt.yticks(range(len(df.index)), list(df.index))
    plt.title(title)
    plt.tight_layout()
    Path("output").mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path

def plot_cooccurrence_network(
    cache: CountsCache,
    min_count: int = 5,
    nodes_subset: Optional[List[str]] = None,
    title: str = "Co-occurrence network",
    output_path: str = "output/cooccurrence_network.png"
) -> str:
    G = nx.Graph()
    # choose nodes
    if nodes_subset is None:
        nodes = list(cache.item_support.keys())
    else:
        nodes = list(nodes_subset)
    for n in nodes:
        G.add_node(n)
    # add edges above threshold
    for p, c in cache.pair_counts.items():
        if c >= min_count:
            a, b = tuple(p)
            if a in nodes and b in nodes:
                G.add_edge(a, b, weight=c)
    pos = nx.spring_layout(G, seed=42, k=0.5)
    plt.figure(figsize=(10, 8))
    nx.draw_networkx_nodes(G, pos, node_color="#4C72B0", node_size=650)
    nx.draw_networkx_labels(G, pos, font_size=9)
    widths = [1 + 0.3*G[u][v]["weight"] for u, v in G.edges()]
    nx.draw_networkx_edges(G, pos, edge_color="#888", width=widths)
    plt.title(title)
    plt.axis("off")
    Path("output").mkdir(exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path
