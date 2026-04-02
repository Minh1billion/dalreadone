import pandas as pd
import traceback

from .operation import BaseStrategy, BaseOperation


class CustomCodeStrategy(BaseStrategy):
    """
    Executes user-supplied Python code to transform a DataFrame.

    The code must define a function `transform(df: pd.DataFrame) -> pd.DataFrame`.
    The function receives the full DataFrame and must return a DataFrame.

    Example:
        def transform(df):
            df = df.copy()
            df['new_col'] = df['a'] + df['b']
            return df
    """

    _ALLOWED_BUILTINS = {
        "abs", "all", "any", "bool", "dict", "enumerate", "filter",
        "float", "int", "isinstance", "len", "list", "map", "max",
        "min", "print", "range", "round", "set", "sorted", "str",
        "sum", "tuple", "type", "zip", "None", "True", "False",
    }

    def __init__(self, code: str) -> None:
        if not code or not code.strip():
            raise ValueError("Custom code cannot be empty")
        self.code = code
        self._fn = None

    def _compile(self) -> None:
        namespace: dict = {
            "__builtins__": {k: __builtins__[k] for k in self._ALLOWED_BUILTINS if k in __builtins__}  # type: ignore[index]
            if isinstance(__builtins__, dict)
            else {k: getattr(__builtins__, k) for k in self._ALLOWED_BUILTINS if hasattr(__builtins__, k)},
            "pd": pd,
        }
        try:
            exec(compile(self.code, "<custom_transform>", "exec"), namespace)  # noqa: S102
        except SyntaxError as e:
            raise ValueError(f"Syntax error in custom code: {e}") from e

        fn = namespace.get("transform")
        if fn is None or not callable(fn):
            raise ValueError("Custom code must define a callable named `transform(df)`")
        self._fn = fn

    def validate(self, df: pd.DataFrame, cols: list[str]) -> None:
        self._compile()

    def fit(self, df: pd.DataFrame, cols: list[str]) -> None:
        if self._fn is None:
            self._compile()

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        if self._fn is None:
            self._compile()
        try:
            result = self._fn(df)
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            user_frames = [f for f in tb if f.filename == "<custom_transform>"]
            if user_frames:
                frame = user_frames[-1]
                location = f"line {frame.lineno}: {frame.line}"
            else:
                location = f"line {tb[-1].lineno}" if tb else "unknown location"
            raise RuntimeError(
                f"{type(e).__name__} at {location}\n{e}"
            ) from e

        if not isinstance(result, pd.DataFrame):
            raise TypeError(
                f"`transform(df)` must return a pd.DataFrame, got {type(result).__name__}"
            )
        return result

    def __repr__(self) -> str:
        preview = self.code[:60].replace("\n", " ")
        return f"CustomCodeStrategy(code={preview!r}...)"


class CustomCodeOperation(BaseOperation):
    pass