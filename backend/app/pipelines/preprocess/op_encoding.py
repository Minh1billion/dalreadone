import pandas as pd

from .operation import BaseStrategy, BaseOperation


class OneHotStrategy(BaseStrategy):
    def __init__(self) -> None:
        self._categories: dict[str, list] = {}

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        super().validate(df, cols)
        numeric = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
        if numeric:
            raise TypeError(f"OneHotStrategy requires categorical columns, got numeric: {numeric}")

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        self._categories = {c: sorted(df[c].dropna().unique().tolist()) for c in cols}

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        dummies = pd.get_dummies(df[cols], columns=cols, dtype=int)
        # align to fitted categories to handle unseen values
        for col, cats in self._categories.items():
            for cat in cats:
                col_name = f"{col}_{cat}"
                if col_name not in dummies.columns:
                    dummies[col_name] = 0
        expected = [f"{c}_{cat}" for c, cats in self._categories.items() for cat in cats]
        return pd.concat([df.drop(columns=cols), dummies[expected]], axis=1)

    def __repr__(self) -> str:
        return "OneHotStrategy()"


class OrdinalStrategy(BaseStrategy):
    def __init__(self, order: dict[str, list] | None = None) -> None:
        self.order = order  # {"col": ["low", "mid", "high"]}
        self._mapping: dict[str, dict] = {}

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        super().validate(df, cols)
        numeric = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
        if numeric:
            raise TypeError(f"OrdinalStrategy requires categorical columns, got numeric: {numeric}")

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        for col in cols:
            cats = self.order.get(col) if self.order else None
            cats = cats or sorted(df[col].dropna().unique().tolist())
            self._mapping[col] = {v: i for i, v in enumerate(cats)}

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
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
        numeric = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
        if numeric:
            raise TypeError(f"LabelStrategy requires categorical columns, got numeric: {numeric}")

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        self._mapping = {
            col: {v: i for i, v in enumerate(sorted(df[col].dropna().unique().tolist()))}
            for col in cols
        }

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        for col in cols:
            df[col] = df[col].map(self._mapping[col])
        return df

    def __repr__(self) -> str:
        return "LabelStrategy()"


class EncodingOperation(BaseOperation):
    pass