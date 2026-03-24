import pandas as pd
import numpy as np

MAX_RETRIES = 3
MAX_RESULT_ROWS = 50


def _serialize_result(result) -> str:
    """
    Convert execution result to a readable string for LLM insight generation.
    Supports: dict of DataFrames/Series/scalars, DataFrame, Series, or scalar.
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


def _exec_code(code: str, df: pd.DataFrame) -> tuple[bool, str, str]:
    """
    Execute pandas code in an isolated local scope.
    Returns: (success, result_str, error_message)
    """
    local_scope = {
        "df": df.copy(),
        "pd": pd,
        "np": np,
    }


    try:
        exec(code, {"__builtins__": {}}, local_scope)

        result = local_scope.get("result")
        if result is None:
            return False, "", "Code did not assign anything to `result`"

        if isinstance(result, dict) and len(result) == 0:
            return False, "", "`result` dict is empty — add at least one key"

        return True, _serialize_result(result), ""

    except Exception as e:
        return False, "", str(e)


def run_with_retry(
    code: str,
    df: pd.DataFrame,
    reprompt_fn,
) -> tuple[str, str]:
    """
    Try executing the code up to MAX_RETRIES times.
    On failure, call reprompt_fn to get a fixed version of the code.
    Returns: (final_result_str, final_code)
    """
    current_code = code

    for attempt in range(1, MAX_RETRIES + 1):
        success, result_str, error = _exec_code(current_code, df)

        if success:
            return result_str, current_code

        if attempt < MAX_RETRIES:
            current_code = reprompt_fn(current_code, error)
        else:
            raise RuntimeError(
                f"Code execution failed after {MAX_RETRIES} attempts. "
                f"Last error: {error}"
            )