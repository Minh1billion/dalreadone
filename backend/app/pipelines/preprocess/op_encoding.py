from __future__ import annotations

import pandas as pd

from .operation import BaseStrategy, BaseOperation

_MAX_NUMERIC_LABEL_CARDINALITY = 50


def _ensure_categorical(
    df: pd.DataFrame,
    cols: list[str],
    strategy_name: str,
) -> pd.DataFrame:
    """
    For each col in cols:
    - If dtype is already non-numeric  -> leave as-is.
    - If dtype is numeric AND cardinality <= threshold -> cast to str silently.
      These are label/ordinal columns that skipped the upstream astype layer.
    - If dtype is numeric AND cardinality >  threshold -> raise TypeError.
      These are genuine continuous columns passed to an encoding strategy by mistake.
    """
    bad: list[str] = []
    df = df.copy()
    for col in cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
        n_unique = df[col].nunique(dropna=True)
        if n_unique <= _MAX_NUMERIC_LABEL_CARDINALITY:
            df[col] = df[col].astype(str)
        else:
            bad.append(col)
    if bad:
        raise TypeError(
            f"{strategy_name} requires categorical columns, got high-cardinality "
            f"numeric columns that look like continuous features: {bad}"
        )
    return df


class OneHotStrategy(BaseStrategy):
    def __init__(self) -> None:
        self._categories: dict[str, list] = {}

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        super().validate(df, cols)

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        df = _ensure_categorical(df, cols, "OneHotStrategy")
        self._categories = {
            c: sorted(df[c].dropna().unique().tolist()) for c in cols
        }

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = _ensure_categorical(df, cols, "OneHotStrategy")
        dummies = pd.get_dummies(df[cols], columns=cols, dtype=int)
        for col, cats in self._categories.items():
            for cat in cats:
                col_name = f"{col}_{cat}"
                if col_name not in dummies.columns:
                    dummies[col_name] = 0
        expected = [
            f"{c}_{cat}"
            for c, cats in self._categories.items()
            for cat in cats
        ]
        return pd.concat([df.drop(columns=cols), dummies[expected]], axis=1)

    def __repr__(self) -> str:
        return "OneHotStrategy()"


class OrdinalStrategy(BaseStrategy):
    def __init__(self, order: dict[str, list] | None = None) -> None:
        self.order = order  # {"col": ["low", "mid", "high"]}
        self._mapping: dict[str, dict] = {}

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        super().validate(df, cols)

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        df = _ensure_categorical(df, cols, "OrdinalStrategy")
        for col in cols:
            cats = self.order.get(col) if self.order else None
            cats = cats or sorted(df[col].dropna().unique().tolist())
            self._mapping[col] = {v: i for i, v in enumerate(cats)}

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = _ensure_categorical(df, cols, "OrdinalStrategy")
        for col in cols:
            df[col] = df[col].map(self._mapping[col])
        return df

    def __repr__(self) -> str:
        return f"OrdinalStrategy(order={self.order})"


class LabelStrategy(BaseStrategy):
    def __init__(self) -> None:
        self._mapping: dict[str, dict] = {}

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        super().validate(df, cols)

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        df = _ensure_categorical(df, cols, "LabelStrategy")
        self._mapping = {
            col: {
                v: i
                for i, v in enumerate(sorted(df[col].dropna().unique().tolist()))
            }
            for col in cols
        }

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = _ensure_categorical(df, cols, "LabelStrategy")
        for col in cols:
            df[col] = df[col].map(self._mapping[col])
        return df

    def __repr__(self) -> str:
        return "LabelStrategy()"


class EncodingOperation(BaseOperation):
    pass