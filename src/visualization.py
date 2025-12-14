
"""
Plotting helpers: bar charts, heatmap, and co-occurrence network.
"""
from __future__ import annotations
from typing import List, Tuple, Optional, Iterable
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.colors
import matplotlib.cm
import math
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
    nodes_subset: Optional[List[str]] = None,
    min_count: int = 50,        # frequency threshold
    min_lift: float = 1.05,     # strength threshold (>1 is positive association)
    top_edges: int = 200,       # cap the number of edges drawn for readability
    title: str = "Co-occurrence network (count & lift thresholds)",
    output_path: str = "output/cooccurrence_network.png",
    seed: int = 42
) -> str:
    """
    Draw a thresholded co-occurrence network:
      - Edge included only if count >= min_count and lift >= min_lift
      - Edge color encodes LIFT (blue->red), width encodes COUNT
      - Node size encodes item support
    """
    # 1) Choose nodes
    if nodes_subset is None:
        nodes = list(cache.item_support.keys())
    else:
        nodes = list(nodes_subset)

    # 2) Build graph with attributes: count, lift
    G = nx.Graph()
    for n in nodes:
        if n in cache.item_support:
            G.add_node(n, support=cache.item_support[n])

    n_tx = max(cache.n_tx, 1)
    p = {n: (cache.item_support.get(n, 0) / n_tx) for n in nodes}

    # Collect candidate edges that meet the thresholds
    edges: List[Tuple[str, str, dict]] = []
    for pair, cnt in cache.pair_counts.items():
        a, b = tuple(pair)
        if a not in G or b not in G:
            continue
        if cnt < min_count:
            continue
        pab = cnt / n_tx
        denom = p[a] * p[b]
        lift = (pab / denom) if denom > 0 else 0.0
        if lift >= min_lift:
            edges.append((a, b, {"count": cnt, "lift": lift}))

    # Limit to top_edges by count (or by lift—pick your preference)
    edges.sort(key=lambda e: (-e[2]["count"], -e[2]["lift"]))
    edges = edges[:top_edges]

    # Add to graph
    G.add_edges_from(edges)

    if G.number_of_edges() == 0:
        # graceful fallback
        Path("output").mkdir(exist_ok=True)
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5,
                 f"No edges pass thresholds (min_count={min_count}, min_lift={min_lift}).",
                 ha="center", va="center")
        plt.axis("off")
        plt.title(title)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return output_path

    # 3) Node sizes (support) with normalization
    supports = [G.nodes[n]["support"] for n in G.nodes()]
    s_min, s_max = (min(supports), max(supports))
    def scale_node(s):
        # map support to 300..1500 points
        if s_max == s_min:
            return 600
        return 300 + 1200 * (s - s_min) / (s_max - s_min)
    node_sizes = [scale_node(G.nodes[n]["support"]) for n in G.nodes()]

    # 4) Edge widths (count) with normalization
    counts = [G.edges[e]["count"] for e in G.edges()]
    c_min, c_max = (min(counts), max(counts))
    def scale_edge(c):
        # map count to 1.0..8.0 px
        if c_max == c_min:
            return 3.0
        return 1.0 + 7.0 * (c - c_min) / (c_max - c_min)
    edge_widths = [scale_edge(G.edges[e]["count"]) for e in G.edges()]

    # 5) Edge colors by lift (colormap)
    lifts = [G.edges[e]["lift"] for e in G.edges()]
    # Clip extreme lifts to keep color scale stable
    lift_low, lift_high = (1.0, max(1.0 + 0.001, min(max(lifts), 2.0)))  # upper bound at ~2
    norm = matplotlib.colors.Normalize(vmin=lift_low, vmax=lift_high)
    cmap = matplotlib.cm.get_cmap("coolwarm")
    edge_colors = [cmap(norm(l)) for l in lifts]

    # 6) Layout & draw
    pos = nx.spring_layout(G, seed=seed, k=0.4, weight=None)  # weight=None = positions not skewed by counts

    fig, ax = plt.subplots(figsize=(10, 8))
    nx.draw_networkx_nodes(
        G, pos,
        node_color="#3b6ea8",
        node_size=node_sizes,
        alpha=0.9,
        linewidths=0.5,
        edgecolors="#1f3c5a",
        ax=ax
    )
    nx.draw_networkx_labels(
        G, pos,
        font_size=9,
        font_color="white",
        bbox=dict(facecolor="#1f3c5a", alpha=0.7, boxstyle="round,pad=0.2"),
        ax=ax
    )
    nx.draw_networkx_edges(
        G, pos,
        width=edge_widths,
        edge_color=edge_colors,
        alpha=0.55,
        arrows=False,
        ax=ax
    )

    # 7) Colorbar for lift
    sm = matplotlib.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Lift (association strength)")

    ax.set_title(title)
    ax.set_axis_off()
    Path("output").mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path

