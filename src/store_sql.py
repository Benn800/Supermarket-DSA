import sqlite3

def save_counts_to_sql(cache, db_path="output/pai_counts.db"):
    con = sqlite3.connect(db_path); cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS item_support(item TEXT PRIMARY KEY, count INT)")
    cur.execute("""CREATE TABLE IF NOT EXISTS pair_counts(
        a TEXT, b TEXT, count INT, PRIMARY KEY(a,b))""")

    # upsert item_support
    for item, cnt in cache.item_support.items():
        cur.execute("INSERT OR REPLACE INTO item_support(item, count) VALUES(?,?)", (item, cnt))

    # upsert pair_counts (order items to keep PK consistent)
    for pair, cnt in cache.pair_counts.items():
        a, b = sorted(tuple(pair))
        cur.execute("INSERT OR REPLACE INTO pair_counts(a, b, count) VALUES(?,?,?)", (a, b, cnt))

    con.commit(); con.close()

def load_top_pairs_from_sql(db_path="output/pai_counts.db", k=10):
    con = sqlite3.connect(db_path); cur = con.cursor()
    cur.execute("SELECT a, b, count FROM pair_counts ORDER BY count DESC LIMIT ?", (k,))
    rows = cur.fetchall()
    con.close()
    return rows

