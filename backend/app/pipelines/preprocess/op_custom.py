from __future__ import annotations
import pandas as pd

from .operation import BaseStrategy, BaseOperation
from app.sandbox.code_executor import CodeExecutor, CodeExecutionError


class CustomCodeStrategy(BaseStrategy):
    def __init__(self, code: str, timeout: int | None = None) -> None:
        if not code or not code.strip():
            raise ValueError("Custom code cannot be empty")
        self.code    = code
        self._executor = CodeExecutor(timeout=timeout)

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        self._executor.validate_ast(self.code)

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        pass

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        result = self._executor.execute(self.code, df)
        return self._executor.validate_output(result)

    def __repr__(self) -> str:
        preview = self.code[:60].replace("\n", " ")
        return f"CustomCodeStrategy(code={preview!r}...)"


class CustomCodeOperation(BaseOperation):
    pass