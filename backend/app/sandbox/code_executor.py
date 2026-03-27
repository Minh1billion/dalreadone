import builtins
import pandas as pd
import numpy as np
import datetime as _datetime
import re

MAX_RETRIES = 3
MAX_RESULT_ROWS = 50

_VALID_CHART_TYPES = {"bar", "line", "pie", "scatter", "histogram", "grouped_bar"}
_DATETIME_MODULE = _datetime

_SAFE_BUILTINS = {
    name: getattr(builtins, name)
    for name in (
        "bool", "bytes", "complex", "dict", "float", "frozenset",
        "int", "list", "set", "str", "tuple",
        "all", "any", "enumerate", "filter", "map", "range",
        "reversed", "sorted", "zip",
        "abs", "callable", "chr", "divmod", "getattr", "hasattr",
        "hash", "id", "isinstance", "issubclass", "iter", "len",
        "max", "min", "next", "ord", "pow", "repr", "round", "sum",
        "format", "print",
        "None", "True", "False",
        "Exception", "ValueError", "TypeError", "KeyError",
        "IndexError", "AttributeError", "StopIteration",
    )
}

_FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"^\s*import\s+",          "Do not use import statements"),
    (r"^\s*from\s+\w+\s+import", "Do not use from...import statements"),
    (r"pd\.read_",              "Do not load files"),
    (r"open\s*\(",              "Do not open files"),
    (r"__import__",             "Do not use __import__"),
    (r"__builtins__",           "Do not access __builtins__"),
    (r"__class__",              "Do not access __class__"),
    (r"__mro__",                "Do not access __mro__"),
    (r"__subclasses__",         "Do not access __subclasses__"),
    (r"__globals__",            "Do not access __globals__"),
    (r"__base__",               "Do not access __base__"),
]

def _validate_code_safety(code: str) -> str | None:
    for pattern, reason in _FORBIDDEN_PATTERNS:
        for line in code.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(pattern, line):
                return (
                    f"Forbidden pattern: `{pattern}`. {reason}. "
                    f"`df` is already a loaded pandas DataFrame."
                )
    return None


def _coerce_to_list(value) -> list | None:
    """
    Convert any list-like (pandas Index, Series, numpy array, plain list)
    to a plain Python list. Returns None if the value is not list-like.
    """
    if isinstance(value, list):
        # Ensure every element is a plain Python scalar
        return [v.item() if hasattr(v, "item") else v for v in value]
    if isinstance(value, (pd.Index, pd.Series, np.ndarray)):
        return value.tolist()
    return None


def _validate_single_chart(chart: dict) -> dict | None:
    if not isinstance(chart, dict):
        return None

    chart_type = chart.get("type")
    labels_raw = chart.get("labels")
    data_raw   = chart.get("data")
    title      = chart.get("title", "")

    if chart_type not in _VALID_CHART_TYPES:
        return None

    # Coerce labels to plain list (handles pd.Index, np.ndarray, etc.)
    labels = _coerce_to_list(labels_raw)
    if labels is None or len(labels) == 0:
        return None

    if data_raw is None or (hasattr(data_raw, "__len__") and len(data_raw) == 0):
        return None

    if chart_type == "grouped_bar":
        series_labels = chart.get("series_labels")
        if not isinstance(series_labels, list) or len(series_labels) == 0:
            return None
        # Coerce each inner series
        coerced_data = []
        for series in data_raw:
            s = _coerce_to_list(series)
            if s is None:
                return None
            if len(s) != len(labels):
                return None
            coerced_data.append(s)
        return {
            "type": chart_type,
            "title": str(title),
            "labels": labels,
            "data": coerced_data,
            "series_labels": series_labels,
        }

    if chart_type == "scatter":
        # data is list of [x, y] pairs - coerce outer list, keep inner pairs
        data = _coerce_to_list(data_raw)
        if data is None:
            return None
        coerced_data = []
        for pair in data:
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                coerced_data.append([
                    pair[0].item() if hasattr(pair[0], "item") else pair[0],
                    pair[1].item() if hasattr(pair[1], "item") else pair[1],
                ])
            else:
                return None
        if len(coerced_data) != len(labels):
            return None
        return {
            "type": chart_type,
            "title": str(title),
            "labels": labels,
            "data": coerced_data,
        }

    # All other types: data is a flat list of numbers
    data = _coerce_to_list(data_raw)
    if data is None or len(data) != len(labels):
        return None

    return {
        "type": chart_type,
        "title": str(title),
        "labels": labels,
        "data": data,
    }


def _extract_charts(result: dict) -> list[dict]:
    charts_raw = result.pop("_charts", None)
    legacy = result.pop("_chart", None)

    candidates = []
    if charts_raw is not None:
        if isinstance(charts_raw, list):
            candidates = charts_raw
        elif isinstance(charts_raw, dict):
            candidates = [charts_raw]
    elif legacy is not None:
        candidates = [legacy] if isinstance(legacy, dict) else []

    validated = []
    for c in candidates:
        v = _validate_single_chart(c)
        if v is not None:
            validated.append(v)

    return validated[:3]


def _serialize_result(result: dict) -> str:
    if isinstance(result, dict):
        sections = []
        for key, val in result.items():
            if isinstance(val, pd.DataFrame):
                rendered = val.head(MAX_RESULT_ROWS).to_markdown(index=True)
            elif isinstance(val, pd.Series):
                rendered = val.head(MAX_RESULT_ROWS).to_string()
            else:
                rendered = str(val)
            sections.append(f"[{key}]\n{rendered}")
        return "\n\n".join(sections)

    if isinstance(result, pd.DataFrame):
        return result.head(MAX_RESULT_ROWS).to_markdown(index=True)

    if isinstance(result, pd.Series):
        return result.head(MAX_RESULT_ROWS).to_string()

    return str(result)


def _exec_code(code: str, df: pd.DataFrame) -> tuple[bool, str, list[dict], str]:
    safety_error = _validate_code_safety(code)
    if safety_error:
        return False, "", [], safety_error

    exec_globals = {
        "__builtins__": _SAFE_BUILTINS,
        "df": df.copy(),
        "pd": pd,
        "np": np,
        "datetime": _DATETIME_MODULE,
    }

    try:
        exec(code, exec_globals)

        result = exec_globals.get("result")
        if result is None:
            return False, "", [], "Code did not assign anything to `result`"

        if isinstance(result, dict) and len(result) == 0:
            return False, "", [], "`result` dict is empty - add at least one key"

        charts = []
        if isinstance(result, dict):
            charts = _extract_charts(result)
            if len(result) == 0:
                return False, "", [], "`result` only had chart keys - add at least one data key"

        return True, _serialize_result(result), charts, ""

    except Exception as e:
        return False, "", [], str(e)


def run_with_retry(
    code: str,
    df: pd.DataFrame,
    reprompt_fn,
) -> tuple[str, list[dict], str]:
    """
    Try executing the code up to MAX_RETRIES times.
    On failure, call reprompt_fn(broken_code, error) to get a fixed version.
    Returns: (final_result_str, charts, final_code)
    """
    current_code = code

    for attempt in range(1, MAX_RETRIES + 1):
        success, result_str, charts, error = _exec_code(current_code, df)

        if success:
            return result_str, charts, current_code

        if attempt < MAX_RETRIES:
            current_code = reprompt_fn(current_code, error)
        else:
            raise RuntimeError(
                f"Code execution failed after {MAX_RETRIES} attempts. "
                f"Last error: {error}"
            )