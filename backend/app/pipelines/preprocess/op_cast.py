from __future__ import annotations
import pandas as pd

from .operation import BaseStrategy, BaseOperation

_SUPPORTED = frozenset({
    "int", "int32", "int64",
    "float", "float32", "float64",
    "str", "string", "object",
    "bool",
    "datetime", "datetime64",
    "category",
})


class CastStrategy(BaseStrategy):
    def __init__(self, dtype_map: dict[str, str]) -> None:
        unsupported = {v for v in dtype_map.values() if v not in _SUPPORTED}
        if unsupported:
            raise ValueError(f"Unsupported dtype(s): {unsupported}. Supported: {_SUPPORTED}")
        self.dtype_map = dtype_map

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(f"Columns not found in DataFrame: {missing}")
        not_mapped = [c for c in cols if c not in self.dtype_map]
        if not_mapped:
            raise ValueError(f"No target dtype specified for columns: {not_mapped}")

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        pass

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        for col in cols:
            target = self.dtype_map[col]
            if target in ("datetime", "datetime64"):
                df[col] = pd.to_datetime(df[col], errors="coerce")
            elif target == "category":
                df[col] = df[col].astype("category")
            elif target in ("str", "string", "object"):
                df[col] = df[col].astype(str)
            elif target == "bool":
                df[col] = df[col].astype(bool)
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype(target)
        return df

    def __repr__(self) -> str:
        return f"CastStrategy(dtype_map={self.dtype_map})"


class CastOperation(BaseOperation):
    pass