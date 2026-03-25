import builtins
import pandas as pd
import numpy as np
import datetime as _datetime

MAX_RETRIES = 3
MAX_RESULT_ROWS = 50

# All chart types the LLM can request
_VALID_CHART_TYPES = {"bar", "line", "pie", "scatter", "histogram", "grouped_bar"}

# Pre-injected datetime so LLM never needs to import it
_DATETIME_MODULE = _datetime

# Safe subset of Python built-ins available inside the sandbox.
# Empty __builtins__ blocks str/int/len/list/range/zip/... which LLM-generated
# pandas code uses constantly — whitelisting is safer than a full block.
_SAFE_BUILTINS = {
    name: getattr(builtins, name)
    for name in (
        # type constructors
        "bool", "bytes", "complex", "dict", "float", "frozenset",
        "int", "list", "set", "str", "tuple",
        # iteration / functional
        "all", "any", "enumerate", "filter", "map", "range",
        "reversed", "sorted", "zip",
        # inspection / comparison
        "abs", "callable", "chr", "divmod", "getattr", "hasattr",
        "hash", "id", "isinstance", "issubclass", "iter", "len",
        "max", "min", "next", "ord", "pow", "repr", "round", "sum",
        # formatting
        "format", "print",
        # singletons
        "None", "True", "False",
        # exceptions LLM code may raise or catch
        "Exception", "ValueError", "TypeError", "KeyError",
        "IndexError", "AttributeError", "StopIteration",
    )
}


def _validate_single_chart(chart: dict) -> dict | None:
    """
    Validate one chart dict.
    Returns the cleaned chart or None if invalid.

    Required keys:
      - type: one of _VALID_CHART_TYPES
      - title: non-empty string
      - labels: list of strings (categories / date strings)
      - data: list of numbers (or list-of-lists for grouped_bar / histogram)

    For grouped_bar, data must be a list of series:
      data = [[v1, v2, ...], [v1, v2, ...]]   -- one inner list per group
      series_labels = ["Group A", "Group B"]  -- required for grouped_bar

    For histogram, labels hold bin edges as strings and data holds counts.
    """
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
        # data is a list of series (list of lists)
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

    # All other types: data is a flat list, same length as labels
    if len(labels) != len(data):
        return None

    return {
        "type": chart_type,
        "title": str(title),
        "labels": labels,
        "data": data,
    }


def _extract_charts(result: dict) -> list[dict]:
    """
    Pop the reserved `_charts` key from the result dict and validate every entry.
    Also accepts the legacy `_chart` key (single dict) for backwards compatibility.

    Returns a list of validated chart dicts (may be empty).
    """
    charts_raw = result.pop("_charts", None)
    legacy = result.pop("_chart", None)

    candidates = []

    # Prefer _charts (new format) over _chart (legacy)
    if charts_raw is not None:
        if isinstance(charts_raw, list):
            candidates = charts_raw
        elif isinstance(charts_raw, dict):
            # LLM accidentally put a single dict instead of a list
            candidates = [charts_raw]
    elif legacy is not None:
        candidates = [legacy] if isinstance(legacy, dict) else []

    validated = []
    for c in candidates:
        v = _validate_single_chart(c)
        if v is not None:
            validated.append(v)

    # Cap at 3 charts per pass to keep responses focused
    return validated[:3]


def _serialize_result(result: dict) -> str:
    """
    Convert execution result to a readable string for LLM insight generation.
    Supports: dict of DataFrames/Series/scalars, DataFrame, Series, or scalar.
    _charts/_chart keys are expected to have been popped before this call.
    """
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
    """
    Execute pandas code in an isolated local scope.
    Returns: (success, result_str, charts, error_message)
    """
    local_scope = {
        "df": df.copy(),
        "pd": pd,
        "np": np,
        # datetime is injected so LLM can use datetime.datetime.now() etc.
        # without needing an import statement (which is blocked)
        "datetime": _DATETIME_MODULE,
    }

    try:
        exec(code, {"__builtins__": _SAFE_BUILTINS}, local_scope)

        result = local_scope.get("result")
        if result is None:
            return False, "", [], "Code did not assign anything to `result`"

        if isinstance(result, dict) and len(result) == 0:
            return False, "", [], "`result` dict is empty — add at least one key"

        # Extract charts before serialising (mutates result dict)
        charts = []
        if isinstance(result, dict):
            charts = _extract_charts(result)

            # After popping chart keys, result might be empty
            if len(result) == 0:
                return (
                    False, "", [],
                    "`result` only had chart keys — add at least one data key"
                )

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