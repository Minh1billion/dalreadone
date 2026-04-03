from __future__ import annotations
import ast
import math
import statistics
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

import pandas as pd

from app.core.config import Config

_ALLOWED_BUILTINS = {
    "abs", "all", "any", "bool", "dict", "enumerate", "filter",
    "float", "int", "isinstance", "len", "list", "map", "max",
    "min", "print", "range", "round", "set", "sorted", "str",
    "sum", "tuple", "type", "zip", "None", "True", "False",
}

_ALLOWED_IMPORTS: dict[str, object] = {
    "math":       math,
    "statistics": statistics,
}

_executor = ThreadPoolExecutor(max_workers=4)


class CodeExecutionError(RuntimeError):
    pass


class CodeExecutor:
    def __init__(self, timeout: int | None = None) -> None:
        self.timeout = timeout or Config.DA_CODE_EXEC_TIMEOUT

    def validate_ast(self, code: str) -> None:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise CodeExecutionError(f"Syntax error: {e}") from e

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # alias.name is e.g. "math" or "math.something"
                    top = alias.name.split(".")[0]
                    if top not in _ALLOWED_IMPORTS:
                        raise CodeExecutionError(
                            f"Import '{alias.name}' is not allowed in custom transform code. "
                            f"Allowed imports: {sorted(_ALLOWED_IMPORTS)}"
                        )
            elif isinstance(node, ast.ImportFrom):
                top = (node.module or "").split(".")[0]
                if top not in _ALLOWED_IMPORTS:
                    raise CodeExecutionError(
                        f"'from {node.module} import ...' is not allowed in custom transform code. "
                        f"Allowed imports: {sorted(_ALLOWED_IMPORTS)}"
                    )

        fn_names = [
            node.name for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]
        if "transform" not in fn_names:
            raise CodeExecutionError(
                "Custom code must define a function named `transform(df)`"
            )

    def _build_namespace(self) -> dict:
        builtins_src = __builtins__ if isinstance(__builtins__, dict) else vars(__builtins__)
        ns = {
            "__builtins__": {
                k: builtins_src[k] for k in _ALLOWED_BUILTINS if k in builtins_src
            },
            "pd": pd,
        }
        ns.update(_ALLOWED_IMPORTS)
        return ns

    def _compile_and_extract(self, code: str) -> object:
        namespace = self._build_namespace()
        exec(compile(code, "<custom_transform>", "exec"), namespace)  # noqa: S102
        return namespace["transform"]

    def execute(self, code: str, df: pd.DataFrame) -> pd.DataFrame:
        fn = self._compile_and_extract(code)

        future = _executor.submit(fn, df)
        try:
            result = future.result(timeout=self.timeout)
        except FutureTimeoutError as e:
            future.cancel()
            raise CodeExecutionError(
                f"Custom transform exceeded timeout of {self.timeout}s"
            ) from e
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            user_frames = [f for f in tb if f.filename == "<custom_transform>"]
            location = (
                f"line {user_frames[-1].lineno}: {user_frames[-1].line}"
                if user_frames
                else f"line {tb[-1].lineno}" if tb else "unknown location"
            )
            raise CodeExecutionError(
                f"{type(e).__name__} at {location}\n{e}"
            ) from e

        return result

    def validate_output(self, result: object) -> pd.DataFrame:
        if not isinstance(result, pd.DataFrame):
            raise CodeExecutionError(
                f"`transform(df)` must return a pd.DataFrame, got {type(result).__name__}"
            )
        return result