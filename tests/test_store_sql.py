import os
from src.analytics import build_counts_cache
from src.store_sql import save_counts_to_sql, load_top_pairs_from_sql

def test_save_and_load_sql(tmp_path):
    tx = [
        ["bread","milk","eggs"],
        ["bread","butter"],
        ["milk","eggs"],
        ["bread","milk"],
        ["butter","jam","bread"],
    ]
    cache = build_counts_cache(tx, max_k=2)
    db_path = tmp_path / "counts.db"

    # Save to SQLite
    save_counts_to_sql(cache, db_path=str(db_path))
    assert os.path.exists(db_path)

    # Load top 3 pairs and check shape
    rows = load_top_pairs_from_sql(db_path=str(db_path), k=3)
    assert len(rows) == 3
    # Rows are (a,b,count)
    for a,b,c in rows:
        assert isinstance(a, str) and isinstance(b, str) and isinstance(c, int)
