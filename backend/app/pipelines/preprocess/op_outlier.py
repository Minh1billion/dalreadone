import pandas as pd
from typing import Literal

from .operation import BaseStrategy, BaseOperation


Action = Literal["clip", "drop"]


class IQRStrategy(BaseStrategy):
    def __init__(self, action: Action = "clip") -> None:
        self.action = action
        self._bounds: dict[str, dict] = {}

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        super().validate(df, cols)
        non_numeric = [c for c in cols if not pd.api.types.is_numeric_dtype(df[c])]
        if non_numeric:
            raise TypeError(f"IQRStrategy requires numeric columns, got: {non_numeric}")

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        q1, q3 = df[cols].quantile(0.25), df[cols].quantile(0.75)
        iqr = q3 - q1
        self._bounds = {
            c: {"lower": (q1 - 1.5 * iqr)[c], "upper": (q3 + 1.5 * iqr)[c]}
            for c in cols
        }

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        if self.action == "clip":
            for col, b in self._bounds.items():
                df[col] = df[col].clip(b["lower"], b["upper"])
        else:
            mask = pd.concat(
                [(df[col] < b["lower"]) | (df[col] > b["upper"]) for col, b in self._bounds.items()],
                axis=1,
            ).any(axis=1)
            df = df[~mask]
        return df

    def __repr__(self) -> str:
        return f"IQRStrategy(action={self.action!r})"


class ZScoreStrategy(BaseStrategy):
    def __init__(self, threshold: float = 3.0, action: Action = "clip") -> None:
        self.threshold = threshold
        self.action = action
        self._stats: dict[str, dict] = {}

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        super().validate(df, cols)
        non_numeric = [c for c in cols if not pd.api.types.is_numeric_dtype(df[c])]
        if non_numeric:
            raise TypeError(f"ZScoreStrategy requires numeric columns, got: {non_numeric}")

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        self._stats = {c: {"mean": df[c].mean(), "std": df[c].std()} for c in cols}

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        if self.action == "clip":
            for col, s in self._stats.items():
                bound = self.threshold * s["std"]
                df[col] = df[col].clip(s["mean"] - bound, s["mean"] + bound)
        else:
            mask = pd.concat(
                [((df[col] - s["mean"]) / s["std"]).abs() > self.threshold for col, s in self._stats.items()],
                axis=1,
            ).any(axis=1)
            df = df[~mask]
        return df

    def __repr__(self) -> str:
        return f"ZScoreStrategy(threshold={self.threshold}, action={self.action!r})"


class PercentileClipStrategy(BaseStrategy):
    def __init__(self, lower: float = 0.05, upper: float = 0.95) -> None:
        if not (0 <= lower < upper <= 1):
            raise ValueError("lower and upper must satisfy 0 <= lower < upper <= 1")
        self.lower = lower
        self.upper = upper
        self._bounds: dict[str, dict] = {}

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        super().validate(df, cols)
        non_numeric = [c for c in cols if not pd.api.types.is_numeric_dtype(df[c])]
        if non_numeric:
            raise TypeError(f"PercentileClipStrategy requires numeric columns, got: {non_numeric}")

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        self._bounds = {
            c: {"lower": df[c].quantile(self.lower), "upper": df[c].quantile(self.upper)}
            for c in cols
        }

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        for col, b in self._bounds.items():
            df[col] = df[col].clip(b["lower"], b["upper"])
        return df

    def __repr__(self) -> str:
        return f"PercentileClipStrategy(lower={self.lower}, upper={self.upper})"


class OutlierOperation(BaseOperation):
    pass