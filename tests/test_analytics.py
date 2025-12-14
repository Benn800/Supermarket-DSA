from src.analytics import (
    build_counts_cache,
    top_copurchases_for_item,
    # top_bundles,
    # pair_stats,
    # cooccurrence_matrix,
)

def sample_tx():
    return [
        ['bread','milk','eggs'],
        ['bread','butter'],
        ['milk','eggs'],
        ['bread','milk'],
        ['butter','jam','bread'],
    ]

def test_top_copurchases_for_bread():
    cache = build_counts_cache(sample_tx(), max_k=3)
    top = dict(top_copurchases_for_item('bread', cache=cache, top_k=10))
    # bread pairs: milk(2), butter(2), eggs(1), jam(1)
    assert top.get('milk') == 2
    assert top.get('butter') == 2
    assert top.get('eggs') == 1
    assert top.get('jam') == 1


