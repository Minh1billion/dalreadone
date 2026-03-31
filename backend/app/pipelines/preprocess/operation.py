from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):
    @abstractmethod
    def fit(self, df: pd.DataFrame, cols: list[str]) -> None: ...

    @abstractmethod
    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame: ...

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(f"Columns not found in DataFrame: {missing}")


class BaseOperation(ABC):
    def __init__(self, strategy: BaseStrategy, cols: list[str] | None = None) -> None:
        self.strategy = strategy
        self.cols = cols
        self._fitted = False

    def _resolve_cols(self, df: pd.DataFrame) -> list[str]:
        return self.cols if self.cols is not None else df.columns.tolist()

    def fit(self, df: pd.DataFrame) -> "BaseOperation":
        cols = self._resolve_cols(df)
        self.strategy.validate(df, cols)
        self.strategy.fit(df, cols)
        self._fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self._fitted:
            raise RuntimeError(f"{self.__class__.__name__} is not fitted yet")
        cols = self._resolve_cols(df)
        return self.strategy.transform(df, cols)

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(strategy={self.strategy}, cols={self.cols})"