"""
TransactionLoader that reads a supermarket CSV and returns a list of baskets (list of items).

This version auto-detects typical column names and groups each transaction by
(Member_number, Date) so items bought together become one basket.

- Deduplicates items within a basket
- Case-insensitive column matching (flexible synonyms)
"""
from __future__ import annotations
from typing import List, Optional
import pandas as pd

class TransactionLoader:
    def __init__(
        self,
        csv_path: str,
        member_cols: Optional[List[str]] = None,
        date_cols: Optional[List[str]] = None,
        item_cols: Optional[List[str]] = None
    ):
        self.csv_path = csv_path
        # Flexible synonyms; you can add more if needed
        self.member_cols = member_cols or [
            "member_number", "membernumber", "member number",
            "member_no", "member", "customer", "customerid", "customer_id"
        ]
        self.date_cols = date_cols or [
            "date", "transaction_date", "order_date", "timestamp"
        ]
        self.item_cols = item_cols or [
            "item name", "item", "itemdescription", "product", "description", "product name"
        ]

    def load_transactions(self) -> List[List[str]]:
        df = pd.read_csv(self.csv_path)

        # Build a case-insensitive lookup {lower_name -> actual_name}
        lower_to_actual = {str(c).strip().lower(): c for c in df.columns}

        member_col = self._first_present(self.member_cols, lower_to_actual)
        date_col   = self._first_present(self.date_cols,   lower_to_actual)
        item_col   = self._first_present(self.item_cols,   lower_to_actual)

        if not (member_col and date_col and item_col):
            raise ValueError(
                "Could not detect required columns. "
                f"Detected columns: {list(df.columns)}. "
                "Expected something like (Member_number, Date, Item name)."
            )

        # Clean & select
        df2 = df[[member_col, date_col, item_col]].dropna()
        df2[item_col] = df2[item_col].astype(str).str.strip()
        # (Optional) normalize spacing/case; comment out if you need original casing:
        # df2[item_col] = df2[item_col].str.lower()

        # Group by (member, date) so items bought together form one basket
        grouped = df2.groupby([member_col, date_col])[item_col].apply(list)

        # Deduplicate items within each basket (preserve order)
        transactions: List[List[str]] = []
        for items in grouped.tolist():
            seen = set()
            dedup = []
            for x in items:
                if x not in seen:
                    seen.add(x)
                    dedup.append(x)
            transactions.append(dedup)

        return transactions

    @staticmethod
    def _first_present(candidates: List[str], lower_to_actual: dict) -> Optional[str]:
        for name in candidates:
            actual = lower_to_actual.get(name.lower())
            if actual:
                return actual
        return None
