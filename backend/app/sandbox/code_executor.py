"""
sandbox/code_executor.py

Safe code execution sandbox for LLM-generated Python.

Security model:
    - __builtins__ is replaced with a curated allowlist (no exec, eval,
      open, __import__, or any I/O primitive)
    - import statements are blocked by static pattern matching before exec
    - A fixed set of safe stdlib modules is pre-injected so LLM code can
      use them without writing import statements (which would be blocked)
    - Only pandas, numpy, re, collections, string, math, itertools,
      functools, operator, and datetime are available

Supported chart types:
    Structured : bar, line, pie, scatter, histogram, grouped_bar
    NLP        : wordcloud_data, sentiment_distribution, top_phrases

Adding a new safe module:
    1. Add it to _STDLIB_MODULES below
    2. Add usage examples to the relevant prompt template if needed
    3. Do NOT add modules with file I/O, network, or subprocess capability

Adding a new chart type:
    1. Add the type string to _STANDARD_CHART_TYPES or _NLP_CHART_TYPES
    2. Add a validator branch in _validate_standard_chart or _validate_nlp_chart
    3. Add a renderer in frontend/components/query/ChartCard.tsx
"""

import builtins
import re
import collections
import string
import math
import itertools
import functools
import operator
import datetime as _datetime
import traceback as _traceback

import pandas as pd
import numpy as np

MAX_RETRIES     = 3
MAX_RESULT_ROWS = 50


# Supported chart types
# Rendered by Chart.js in ChartCard
_STANDARD_CHART_TYPES = {
    "bar", "line", "pie", "scatter", "histogram", "grouped_bar",
}

# Rendered by custom components in ChartCard
_NLP_CHART_TYPES = {
    "wordcloud_data",          # list of {word, weight} → tag cloud
    "sentiment_distribution",  # {positive, negative, neutral} → donut
    "top_phrases",             # labels + scores → horizontal bar
}

_VALID_CHART_TYPES = _STANDARD_CHART_TYPES | _NLP_CHART_TYPES


# Builtins allowlist
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


# Pre-injected stdlib modules
# Available in generated code without import statements.
_STDLIB_MODULES = {
    "re":          re,
    "collections": collections,
    "string":      string,
    "math":        math,
    "itertools":   itertools,
    "functools":   functools,
    "operator":    operator,
    "datetime":    _datetime,
}


# Static safety checks
_FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"^\s*import\s+",             "Do not use import statements"),
    (r"^\s*from\s+\w+\s+import",  "Do not use from...import statements"),
    (r"pd\.read_",                 "Do not load files"),
    (r"open\s*\(",                 "Do not open files"),
    (r"__import__",                "Do not use __import__"),
    (r"__builtins__",              "Do not access __builtins__"),
    (r"__class__",                 "Do not access __class__"),
    (r"__mro__",                   "Do not access __mro__"),
    (r"__subclasses__",            "Do not access __subclasses__"),
    (r"__globals__",               "Do not access __globals__"),
    (r"__base__",                  "Do not access __base__"),
]


def _validate_code_safety(code: str) -> str | None:
    """
    Run static pattern checks before exec.
    Returns an error string if forbidden, else None.
    """
    for pattern, reason in _FORBIDDEN_PATTERNS:
        for line in code.splitlines():
            if line.strip().startswith("#"):
                continue
            if re.search(pattern, line):
                return (
                    f"Forbidden pattern: `{pattern}`. {reason}. "
                    f"`df` is already a loaded pandas DataFrame."
                )
    return None


# NaN / Inf sanitization
def _sanitize_float(v):
    """
    Convert a single float-like value to a JSON-safe Python float.
    NaN  → None
    ±Inf → None
    """
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if hasattr(v, "item"):          # numpy scalar
        f = float(v.item())
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    return v


def _sanitize_list(lst: list) -> list:
    """Recursively sanitize every element of a flat or nested list."""
    out = []
    for item in lst:
        if isinstance(item, list):
            out.append(_sanitize_list(item))
        else:
            out.append(_sanitize_float(item))
    return out


# Result coercion helpers
def _coerce_to_list(value) -> list | None:
    """Convert any list-like to a plain Python list of scalars."""
    if isinstance(value, list):
        return [v.item() if hasattr(v, "item") else v for v in value]
    if isinstance(value, (pd.Index, pd.Series, np.ndarray)):
        return value.tolist()
    return None


def _coerce_scalar(value) -> float | None:
    """Coerce a numpy scalar or plain number to JSON-safe Python float."""
    raw = float(value.item() if hasattr(value, "item") else value)
    if math.isnan(raw) or math.isinf(raw):
        return None
    return raw


# Chart validators — standard
def _validate_standard_chart(
    chart: dict,
    chart_type: str,
    labels: list,
    data_raw,
) -> dict | None:
    """Validate bar, line, pie, scatter, histogram, grouped_bar."""
    title = str(chart.get("title", ""))

    if chart_type == "grouped_bar":
        series_labels = chart.get("series_labels")
        if not isinstance(series_labels, list) or len(series_labels) == 0:
            return None
        coerced_data = []
        for series in data_raw:
            s = _coerce_to_list(series)
            if s is None or len(s) != len(labels):
                return None
            coerced_data.append(_sanitize_list(s))
        return {
            "type":          chart_type,
            "title":         title,
            "labels":        labels,
            "data":          coerced_data,
            "series_labels": series_labels,
        }

    if chart_type == "scatter":
        data = _coerce_to_list(data_raw)
        if data is None:
            return None
        coerced = []
        for pair in data:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                return None
            try:
                x = _coerce_scalar(pair[0])
                y = _coerce_scalar(pair[1])
            except (TypeError, ValueError):
                # Non-numeric axis value (e.g. string category) — drop entire chart
                return None
            if x is None or y is None:
                continue  # skip NaN/Inf points
            coerced.append([x, y])
        if not coerced:
            return None
        # Pass color_by through so frontend can colour points by group
        color_by_raw = chart.get("color_by")
        color_by = (
            [str(v) for v in color_by_raw]
            if isinstance(color_by_raw, list) and len(color_by_raw) == len(data)
            else None
        )
        out = {"type": chart_type, "title": title, "labels": labels, "data": coerced}
        if color_by is not None:
            out["color_by"] = color_by
        return out

    # bar, line, pie, histogram
    data = _coerce_to_list(data_raw)
    if data is None or len(data) != len(labels):
        return None
    return {
        "type":   chart_type,
        "title":  title,
        "labels": labels,
        "data":   _sanitize_list(data),
    }


# Chart validators — NLP
def _validate_nlp_chart(chart: dict, chart_type: str) -> dict | None:
    """
    Validate NLP-specific chart types.

    wordcloud_data
        Expected shape:
            { type: "wordcloud_data", title: str,
              items: [ { word: str, weight: float }, ... ] }

    sentiment_distribution
        Expected shape:
            { type: "sentiment_distribution", title: str,
              positive: float, negative: float, neutral: float }
        Values are percentages (0-100). They do not need to sum to 100
        exactly (rounding is fine).

    top_phrases
        Expected shape:
            { type: "top_phrases", title: str,
              labels: list[str], data: list[float] }
        Rendered as a horizontal bar chart. Labels are phrases,
        data values are scores or counts.
    """
    title = str(chart.get("title", ""))

    if chart_type == "wordcloud_data":
        items = chart.get("items")
        if not isinstance(items, list) or len(items) == 0:
            return None
        coerced = []
        for item in items:
            if not isinstance(item, dict):
                return None
            word   = item.get("word")
            weight = item.get("weight")
            if not isinstance(word, str) or weight is None:
                return None
            safe_weight = _coerce_scalar(weight)
            if safe_weight is None:
                continue            # skip words with NaN/Inf weight
            coerced.append({"word": word, "weight": safe_weight})
        if not coerced:
            return None
        return {"type": chart_type, "title": title, "items": coerced}

    if chart_type == "sentiment_distribution":
        pos = chart.get("positive")
        neg = chart.get("negative")
        neu = chart.get("neutral")
        if any(v is None for v in (pos, neg, neu)):
            return None
        safe_pos = _coerce_scalar(pos)
        safe_neg = _coerce_scalar(neg)
        safe_neu = _coerce_scalar(neu)
        if any(v is None for v in (safe_pos, safe_neg, safe_neu)):
            return None
        return {
            "type":     chart_type,
            "title":    title,
            "positive": safe_pos,
            "negative": safe_neg,
            "neutral":  safe_neu,
        }

    if chart_type == "top_phrases":
        labels = _coerce_to_list(chart.get("labels"))
        data   = _coerce_to_list(chart.get("data"))
        if not labels or not data or len(labels) != len(data):
            return None
        return {
            "type":   chart_type,
            "title":  title,
            "labels": labels,
            "data":   _sanitize_list(data),
        }

    return None


# Chart dispatcher
def _validate_single_chart(chart: dict) -> dict | None:
    """
    Dispatch to the correct validator based on chart type.
    Returns None if the chart is malformed or has an unsupported type.
    """
    if not isinstance(chart, dict):
        return None

    chart_type = chart.get("type")
    if chart_type not in _VALID_CHART_TYPES:
        return None

    if chart_type in _NLP_CHART_TYPES:
        return _validate_nlp_chart(chart, chart_type)

    data_raw = chart.get("data")
    if data_raw is None or (hasattr(data_raw, "__len__") and len(data_raw) == 0):
        return None

    labels_raw = chart.get("labels")
    labels     = _coerce_to_list(labels_raw) or []

    # Scatter uses x/y pairs — labels are optional and can be empty
    if chart_type != "scatter" and len(labels) == 0:
        return None

    return _validate_standard_chart(chart, chart_type, labels, data_raw)


def _extract_charts(result: dict) -> list[dict]:
    """
    Extract and validate chart dicts from result.
    Accepts `_charts` (list) or legacy `_chart` (single dict).
    Returns at most 3 validated charts.
    """
    charts_raw = result.pop("_charts", None)
    legacy     = result.pop("_chart", None)

    candidates: list = []
    if charts_raw is not None:
        candidates = charts_raw if isinstance(charts_raw, list) else [charts_raw]
    elif legacy is not None:
        candidates = [legacy] if isinstance(legacy, dict) else []

    validated = [v for c in candidates if (v := _validate_single_chart(c)) is not None]
    return validated[:3]


# Result serialization
def _sanitize_for_markdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace NaN / ±Inf in a DataFrame with None so to_markdown()
    produces clean output without non-JSON floats leaking through.
    """
    return df.where(pd.notnull(df), other=None)


def _serialize_result(result) -> str:
    if isinstance(result, dict):
        sections = []
        for key, val in result.items():
            if isinstance(val, pd.DataFrame):
                rendered = _sanitize_for_markdown(val.head(MAX_RESULT_ROWS)).to_markdown(index=True)
            elif isinstance(val, pd.Series):
                rendered = val.head(MAX_RESULT_ROWS).fillna("").to_string()
            else:
                rendered = str(val)
            sections.append(f"[{key}]\n{rendered}")
        return "\n\n".join(sections)

    if isinstance(result, pd.DataFrame):
        return _sanitize_for_markdown(result.head(MAX_RESULT_ROWS)).to_markdown(index=True)
    if isinstance(result, pd.Series):
        return result.head(MAX_RESULT_ROWS).fillna("").to_string()
    return str(result)


# Error enrichment
def _build_error_message(exc: Exception, code: str) -> str:
    """
    Build an error string that includes:
      - the exception type and message
      - the line number inside the generated code where it occurred
      - the actual offending source line

    This gives the reprompt LLM enough context to fix the code without
    guessing which line is wrong.
    """
    tb = _traceback.extract_tb(exc.__traceback__)
    code_lines = code.splitlines()

    # Walk the traceback frames from innermost outward, find the first frame
    # whose source is "<string>" (i.e. exec'd code) and whose lineno is valid.
    offending_line = None
    lineno         = None
    for frame in reversed(tb):
        if frame.filename == "<string>" and frame.lineno is not None:
            lineno = frame.lineno
            idx    = lineno - 1
            if 0 <= idx < len(code_lines):
                offending_line = code_lines[idx].strip()
            break

    parts = [f"{type(exc).__name__}: {exc}"]
    if lineno is not None:
        parts.append(f"  at line {lineno}: {offending_line or '(unknown)'}")

    # Common fix hints injected directly into the error so the reprompt
    # template doesn't need to know about every edge case.
    msg = str(exc)
    if "indices must be integers or slices, not Series" in msg:
        parts.append(
            "Fix: you are using a pandas Series as a list index. "
            "Use .iloc[int] or convert to a Python int first. "
            "Example: use `df2.iloc[0]['col']` not `df2[series]['col']`."
        )
    elif "observed" in msg:
        parts.append(
            "Fix: add observed=True to groupby() to silence FutureWarning "
            "and avoid phantom NaN groups. "
            "Example: df.groupby('col', observed=True)['val'].mean()"
        )
    elif "not JSON compliant" in msg or "Out of range float" in msg:
        parts.append(
            "Fix: your result contains NaN or Inf values. "
            "Drop or fill them before assigning to result. "
            "Example: series.fillna(0) or df.dropna()"
        )

    return "\n".join(parts)


# Core exec
def _exec_code(
    code: str,
    df: pd.DataFrame,
    extra_globals: dict | None = None,
) -> tuple[bool, str, list[dict], str]:
    """
    Execute generated code in the sandbox.

    Args:
        code          : LLM-generated code string.
        df            : DataFrame exposed as `df`.
        extra_globals : Extra variables to inject (e.g. nlp_features).

    Returns:
        (success, result_str, charts, error_message)
    """
    safety_error = _validate_code_safety(code)
    if safety_error:
        return False, "", [], safety_error

    # Subclass DataFrame used inside the sandbox so groupby always defaults
    # to observed=True — prevents phantom NaN groups (FutureWarning) without
    # touching the global pd.DataFrame class.
    class _SandboxDF(pd.DataFrame):
        def groupby(self, by, **kwargs):
            kwargs.setdefault("observed", True)
            return super().groupby(by, **kwargs)

    exec_globals: dict = {
        "__builtins__": _SAFE_BUILTINS,
        "df":           _SandboxDF(df),
        "pd":           pd,
        "np":           np,
        **_STDLIB_MODULES,
    }
    if extra_globals:
        exec_globals.update(extra_globals)

    try:
        exec(code, exec_globals)

        result = exec_globals.get("result")
        if result is None:
            return False, "", [], "Code did not assign anything to `result`"
        if isinstance(result, dict) and len(result) == 0:
            return False, "", [], "`result` dict is empty — add at least one key"

        charts: list[dict] = []
        if isinstance(result, dict):
            charts = _extract_charts(result)
            if len(result) == 0:
                return False, "", [], "`result` only had chart keys — add at least one data key"

        return True, _serialize_result(result), charts, ""

    except Exception as e:
        error_msg = _build_error_message(e, code)
        return False, "", [], error_msg


def run_with_retry(
    code: str,
    df: pd.DataFrame,
    reprompt_fn,
    extra_globals: dict | None = None,
) -> tuple[str, list[dict], str]:
    """
    Execute generated code, retrying up to MAX_RETRIES times.

    Args:
        code          : Initial generated code.
        df            : DataFrame exposed as `df`.
        reprompt_fn   : Callable(broken_code, error) -> fixed_code.
        extra_globals : Extra sandbox variables (e.g. nlp_features).

    Returns:
        (result_str, charts, final_code)

    Raises:
        RuntimeError if all retries are exhausted.
    """
    current_code = code

    for attempt in range(1, MAX_RETRIES + 1):
        success, result_str, charts, error = _exec_code(
            current_code, df, extra_globals=extra_globals
        )
        if success:
            return result_str, charts, current_code

        if attempt < MAX_RETRIES:
            current_code = reprompt_fn(current_code, error)
        else:
            raise RuntimeError(
                f"Code execution failed after {MAX_RETRIES} attempts. "
                f"Last error: {error}"
            )