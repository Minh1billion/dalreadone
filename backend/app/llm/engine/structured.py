"""
engine/structured.py

LLM call wrappers for the structured (tabular/numeric) pipeline.
All prompt variables are truncated before being sent to keep
token usage within budget.
"""

from typing import Optional

from app.llm.cost_tracker import CostTracker
from app.llm.engine.base import (
    invoke,
    parse_code_response,
    truncate,
    MAX_SCHEMA_CHARS,
    MAX_SAMPLE_ROWS_CHARS,
    MAX_STATS_CHARS,
    MAX_RESULT_CHARS,
    INTERESTING_MIN_CHARS,
)


def generate_code(
    context: dict,
    user_question: str = "",
    tracker: Optional[CostTracker] = None,
) -> tuple[str, str]:
    """
    Pass-1: generate exploratory analysis code for a structured dataset.

    Returns:
        (explore_reason, python_code)
    """
    raw = invoke(
        "generate_code.txt",
        {
            "filename":      context["filename"],
            "schema":        truncate(context["schema"],      MAX_SCHEMA_CHARS),
            "sample_rows":   truncate(context["sample_rows"], MAX_SAMPLE_ROWS_CHARS),
            "stats":         truncate(context["stats"],       MAX_STATS_CHARS),
            "user_question": user_question or "No specific question — explore freely.",
        },
        stage="generate_code",
        tracker=tracker,
    )
    return parse_code_response(raw)


def generate_interesting_code(
    context: dict,
    explore_reason: str,
    result_str: str,
    user_question: str = "",
    tracker: Optional[CostTracker] = None,
) -> tuple[str, str]:
    """
    Pass-2: generate code to dig into anomalies or interesting findings.
    Returns ("", "") if pass-1 result is too short to be worth a second pass.

    Returns:
        (interesting_reason, python_code)
    """
    if len(result_str) < INTERESTING_MIN_CHARS:
        return "", ""

    raw = invoke(
        "find_interesting.txt",
        {
            "filename":       context["filename"],
            "schema":         truncate(context["schema"],     MAX_SCHEMA_CHARS),
            "explore_reason": explore_reason,
            "result":         truncate(result_str,            MAX_RESULT_CHARS),
            "user_question":  user_question or "No specific question provided.",
        },
        stage="find_interesting",
        tracker=tracker,
    )
    return parse_code_response(raw)


def reprompt_code(
    context: dict,
    broken_code: str,
    error: str,
    tracker: Optional[CostTracker] = None,
    stage: str = "reprompt_code",
) -> str:
    """
    Ask the LLM to fix broken code after a failed sandbox execution.

    Returns:
        Fixed python_code string (no explore_reason needed here).
    """
    raw = invoke(
        "fix_code.txt",
        {
            "filename":    context["filename"],
            "schema":      truncate(context["schema"], MAX_SCHEMA_CHARS),
            "broken_code": broken_code,
            "error":       error,
        },
        stage=stage,
        tracker=tracker,
    )
    # Reuse parse_code_response by prefixing a dummy EXPLORE line
    _, code = parse_code_response(f"EXPLORE: fix\n{raw}")
    return code