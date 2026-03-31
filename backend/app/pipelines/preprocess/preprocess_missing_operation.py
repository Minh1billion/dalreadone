import pandas as pd
from typing import Any

from .operation import BaseStrategy, BaseOperation


class MeanStrategy(BaseStrategy):
    def __init__(self) -> None:
        self._params: dict[str, float] = {}

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        super().validate(df, cols)
        non_numeric = [c for c in cols if not pd.api.types.is_numeric_dtype(df[c])]
        if non_numeric:
            raise TypeError(f"MeanStrategy requires numeric columns, got: {non_numeric}")

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        self._params = df[cols].mean().to_dict()

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        df[cols] = df[cols].fillna({c: self._params[c] for c in cols})
        return df

    def __repr__(self) -> str:
        return "MeanStrategy()"


class MedianStrategy(BaseStrategy):
    def __init__(self) -> None:
        self._params: dict[str, float] = {}

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        super().validate(df, cols)
        non_numeric = [c for c in cols if not pd.api.types.is_numeric_dtype(df[c])]
        if non_numeric:
            raise TypeError(f"MedianStrategy requires numeric columns, got: {non_numeric}")

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        self._params = df[cols].median().to_dict()

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        df[cols] = df[cols].fillna({c: self._params[c] for c in cols})
        return df

    def __repr__(self) -> str:
        return "MedianStrategy()"


class ModeStrategy(BaseStrategy):
    def __init__(self) -> None:
        self._params: dict[str, Any] = {}

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        self._params = df[cols].mode().iloc[0].to_dict()

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        df[cols] = df[cols].fillna({c: self._params[c] for c in cols})
        return df

    def __repr__(self) -> str:
        return "ModeStrategy()"


class ConstantStrategy(BaseStrategy):
    def __init__(self, fill_value: Any | dict[str, Any] = 0) -> None:
        self.fill_value = fill_value

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        pass

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        df = df.copy()
        values = (
            self.fill_value
            if isinstance(self.fill_value, dict)
            else {c: self.fill_value for c in cols}
        )
        df[cols] = df[cols].fillna(values)
        return df

    def __repr__(self) -> str:
        return f"ConstantStrategy(fill_value={self.fill_value})"


class DropRowStrategy(BaseStrategy):
    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        pass

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        return df.dropna(subset=cols).copy()

    def __repr__(self) -> str:
        return "DropRowStrategy()"


class DropColStrategy(BaseStrategy):
    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        pass

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        return df.drop(columns=cols).copy()

    def __repr__(self) -> str:
        return "DropColStrategy()"


class MissingOperation(BaseOperation):
    pass