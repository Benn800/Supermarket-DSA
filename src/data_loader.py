"""
TransactionLoader that reads a supermarket CSV and returns a list of baskets (list of items).
Preferred schema: rows with columns ['Transaction', 'Item'].
Fallbacks:
- Single column with comma/semicolon-separated items.
- If multiple columns exist, take non-null string columns per row as a basket.
"""
from __future__ import annotations
from typing import List
import pandas as pd

class TransactionLoader:
    def __init__(self, csv_path: str, transaction_col: str = "Transaction", item_col: str = "Item"):
        self.csv_path = csv_path
        self.transaction_col = transaction_col
        self.item_col = item_col

    def load_transactions(self) -> List[List[str]]:
        df = pd.read_csv(self.csv_path)

        # Preferred: (Transaction, Item)
        if self.transaction_col in df.columns and self.item_col in df.columns:
            df = df[[self.transaction_col, self.item_col]].dropna()
            df[self.item_col] = df[self.item_col].astype(str).str.strip()
            grouped = df.groupby(self.transaction_col)[self.item_col].apply(list).reset_index(drop=True)
            return [self._dedupe_keep_order(items) for items in grouped.tolist()]

        # Single column with comma/semicolon-separated items
        possible_cols = [c for c in df.columns if df[c].dtype == object]
        if len(possible_cols) == 1:
            col = possible_cols[0]
            baskets: List[List[str]] = []
            for v in df[col].dropna().astype(str):
                parts = [p.strip() for p in v.replace(";", ",").split(",") if p.strip()]
                baskets.append(self._dedupe_keep_order(parts))
            return baskets

        # Fallback: treat non-null string cells across columns in a row as a basket
        baskets: List[List[str]] = []
        for _, row in df.iterrows():
            items = []
            for c in df.columns:
                val = row[c]
                if isinstance(val, str) and val.strip():
                    items.append(val.strip())
            if items:
                baskets.append(self._dedupe_keep_order(items))
        return baskets

    @staticmethod
    def _dedupe_keep_order(items: List[str]) -> List[str]:
        seen = set()
        out = []
        for x in items:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out
