import pickle
import pandas as pd
from pathlib import Path

from .operation import BaseOperation


class Pipeline:
    def __init__(self) -> None:
        self._steps: list[BaseOperation] = []

    def add(self, operation: BaseOperation) -> "Pipeline":
        self._steps.append(operation)
        return self

    def fit(self, df: pd.DataFrame) -> "Pipeline":
        for step in self._steps:
            step.fit(df)
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        for step in self._steps:
            df = step.transform(df)
        return df

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        for step in self._steps:
            df = step.fit_transform(df)
        return df

    def save(self, path: str | Path) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str | Path) -> "Pipeline":
        with open(path, "rb") as f:
            return pickle.load(f)

    def __repr__(self) -> str:
        steps = "\n  ".join(f"[{i}] {s}" for i, s in enumerate(self._steps))
        return f"Pipeline(\n  {steps}\n)"