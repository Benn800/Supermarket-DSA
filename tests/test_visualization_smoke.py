import os
from src.analytics import build_counts_cache, top_copurchases_for_item, top_bundles, cooccurrence_matrix
from functions.visualization import (
    plot_top_copurchases_bar, plot_top_bundles_bar, plot_cooccurrence_heatmap, plot_cooccurrence_network
)

def sample_tx():
    return [
        ['bread','milk','eggs'],
        ['bread','butter'],
        ['milk','eggs'],
        ['bread','milk'],
        ['butter','jam','bread'],
    ]

def test_plots_smoke():
    cache = build_counts_cache(sample_tx(), max_k=3)
    pairs = top_copurchases_for_item('bread', cache=cache, top_k=5)
    bundles = top_bundles(cache=cache, top_n=5, include_trios=True)
    df = cooccurrence_matrix(cache)

    p1 = plot_top_copurchases_bar('bread', pairs)
    p2 = plot_top_bundles_bar(bundles)
    p3 = plot_cooccurrence_heatmap(df)
    p4 = plot_cooccurrence_network(cache, min_count=1)

    assert os.path.exists(p1)
    assert os.path.exists(p2)
    assert os.path.exists(p3)
    assert os.path.exists(p4)