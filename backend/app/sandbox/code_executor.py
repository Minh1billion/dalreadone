import builtins
import pandas as pd
import numpy as np
import datetime as _datetime

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
    ("pd.read_csv",    "Do not load files - `df` is already provided."),
    ("pd.read_excel",  "Do not load files - `df` is already provided."),
    ("pd.read_",       "Do not load files - `df` is already provided."),
    ("open(",          "Do not open files - `df` is already provided."),
    ("read_csv(",      "Do not load files - `df` is already provided."),
    ("read_excel(",    "Do not load files - `df` is already provided."),
    ("import ",        "Do not use import statements - pd, np, datetime are pre-loaded."),
    ("from ",          "Do not use import statements - pd, np, datetime are pre-loaded."),
    ("__import__",     "Do not use __import__."),
    ("__builtins__",   "Do not access __builtins__."),
    ("__class__",      "Do not access __class__ or use MRO-based introspection."),
    ("__mro__",        "Do not access __mro__."),
    ("__subclasses__", "Do not access __subclasses__."),
    ("__globals__",    "Do not access __globals__."),
    ("__base__",       "Do not access __base__."),
]


def _validate_code_safety(code: str) -> str | None:
    for pattern, reason in _FORBIDDEN_PATTERNS:
        if pattern in code:
            return (
                f"Forbidden pattern detected: `{pattern}`. {reason} "
                f"Remember: `df` is already a loaded pandas DataFrame. "
                f"Never read files or import modules inside the generated code."
            )
    return None


def _validate_single_chart(chart: dict) -> dict | None:
    if not isinstance(chart, dict):
        return None

    chart_type = chart.get("type")
    labels = chart.get("labels")
    data = chart.get("data")
    title = chart.get("title", "")

    if chart_type not in _VALID_CHART_TYPES:
        return None
    if not isinstance(labels, list) or not isinstance(data, list):
        return None
    if len(labels) == 0 or len(data) == 0:
        return None

    if chart_type == "grouped_bar":
        series_labels = chart.get("series_labels")
        if not isinstance(series_labels, list) or len(series_labels) == 0:
            return None
        for series in data:
            if not isinstance(series, list):
                return None
            if len(series) != len(labels):
                return None
        return {
            "type": chart_type,
            "title": str(title),
            "labels": labels,
            "data": data,
            "series_labels": series_labels,
        }

    if len(labels) != len(data):
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