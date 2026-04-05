from __future__ import annotations
import pandas as pd

from .operation import BaseStrategy, BaseOperation


class DropColumnsStrategy(BaseStrategy):
    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        pass

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        return df.drop(columns=cols).copy()

    def __repr__(self) -> str:
        return "DropColumnsStrategy()"


class DropDuplicatesStrategy(BaseStrategy):
    def __init__(self, keep: str = "first") -> None:
        if keep not in ("first", "last", False):
            raise ValueError("keep must be 'first', 'last', or False")
        self.keep = keep

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(f"Columns not found in DataFrame: {missing}")

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        pass

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        subset = cols if cols else None
        return df.drop_duplicates(subset=subset, keep=self.keep).copy()

    def __repr__(self) -> str:
        return f"DropDuplicatesStrategy(keep={self.keep!r})"


class DropOperation(BaseOperation):
    pass