from __future__ import annotations
from typing import Callable
import pandas as pd

import dill

from .operation import BaseStrategy, BaseOperation


class LambdaStrategy(BaseStrategy):
    def __init__(self, expressions: list[dict[str, str | Callable]]) -> None:
        for expr in expressions:
            if "output_col" not in expr:
                raise ValueError(f"Expression missing 'output_col': {expr}")
            if "fn" not in expr or not callable(expr["fn"]):
                raise ValueError(f"Expression missing callable 'fn': {expr}")
        self.expressions = expressions

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        pass

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        pass

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        for expr in self.expressions:
            try:
                df[expr["output_col"]] = expr["fn"](df)
            except Exception as e:
                raise RuntimeError(
                    f"Error computing '{expr['output_col']}': {e}"
                ) from e
        return df

    def __getstate__(self) -> dict:
        return {
            "expressions": [
                {"output_col": e["output_col"], "fn": dill.dumps(e["fn"])}
                for e in self.expressions
            ]
        }

    def __setstate__(self, state: dict) -> None:
        self.expressions = [
            {"output_col": e["output_col"], "fn": dill.loads(e["fn"])}
            for e in state["expressions"]
        ]

    def __repr__(self) -> str:
        cols = [e["output_col"] for e in self.expressions]
        return f"LambdaStrategy(outputs={cols})"


class BinningStrategy(BaseStrategy):
    def __init__(self, bins_map: dict[str, dict]) -> None:
        for col, cfg in bins_map.items():
            for key in ("output_col", "bins"):
                if key not in cfg:
                    raise ValueError(f"bins_map['{col}'] missing key '{key}'")
        self.bins_map = bins_map

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(f"Columns not found in DataFrame: {missing}")

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        pass

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        for col in cols:
            cfg = self.bins_map[col]
            df[cfg["output_col"]] = pd.cut(
                df[col],
                bins=cfg["bins"],
                labels=cfg.get("labels"),
                right=cfg.get("right", True),
                include_lowest=True,
            )
        return df

    def __repr__(self) -> str:
        return f"BinningStrategy(bins_map={self.bins_map})"


class FeatureOperation(BaseOperation):
    pass