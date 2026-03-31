import pandas as pd

from .operation import BaseStrategy, BaseOperation


class MinMaxStrategy(BaseStrategy):
    def __init__(self, feature_range: tuple[float, float] = (0.0, 1.0)) -> None:
        self.feature_range = feature_range
        self._params: dict[str, dict] = {}

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        super().validate(df, cols)
        non_numeric = [c for c in cols if not pd.api.types.is_numeric_dtype(df[c])]
        if non_numeric:
            raise TypeError(f"MinMaxStrategy requires numeric columns, got: {non_numeric}")

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        self._params = {c: {"min": df[c].min(), "max": df[c].max()} for c in cols}

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        lo, hi = self.feature_range
        for col, p in self._params.items():
            denom = p["max"] - p["min"]
            scaled = (df[col] - p["min"]) / denom if denom != 0 else 0.0
            df[col] = scaled * (hi - lo) + lo
        return df

    def __repr__(self) -> str:
        return f"MinMaxStrategy(feature_range={self.feature_range})"


class StandardStrategy(BaseStrategy):
    def __init__(self) -> None:
        self._params: dict[str, dict] = {}

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        super().validate(df, cols)
        non_numeric = [c for c in cols if not pd.api.types.is_numeric_dtype(df[c])]
        if non_numeric:
            raise TypeError(f"StandardStrategy requires numeric columns, got: {non_numeric}")

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        self._params = {c: {"mean": df[c].mean(), "std": df[c].std()} for c in cols}

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        for col, p in self._params.items():
            df[col] = (df[col] - p["mean"]) / p["std"] if p["std"] != 0 else 0.0
        return df

    def __repr__(self) -> str:
        return "StandardStrategy()"


class RobustStrategy(BaseStrategy):
    def __init__(self) -> None:
        self._params: dict[str, dict] = {}

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        super().validate(df, cols)
        non_numeric = [c for c in cols if not pd.api.types.is_numeric_dtype(df[c])]
        if non_numeric:
            raise TypeError(f"RobustStrategy requires numeric columns, got: {non_numeric}")

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        self._params = {
            c: {
                "median": df[c].median(),
                "iqr": df[c].quantile(0.75) - df[c].quantile(0.25),
            }
            for c in cols
        }

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        for col, p in self._params.items():
            df[col] = (df[col] - p["median"]) / p["iqr"] if p["iqr"] != 0 else 0.0
        return df

    def __repr__(self) -> str:
        return "RobustStrategy()"


class ScalingOperation(BaseOperation):
    pass