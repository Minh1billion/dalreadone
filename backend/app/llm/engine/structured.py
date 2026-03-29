from typing import Optional

from app.llm.cost_tracker import CostTracker
from app.llm.engine.base import (
    invoke, parse_code_response, truncate,
    MAX_SCHEMA_CHARS, MAX_SAMPLE_ROWS_CHARS, MAX_STATS_CHARS,
    MAX_RESULT_CHARS, INTERESTING_MIN_CHARS,
)


def generate_code(
    context: dict,
    user_question: str = "",
    tracker: Optional[CostTracker] = None,
    api_key: str = None,
) -> tuple[str, str]:
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
        api_key=api_key,
    )
    return parse_code_response(raw)


def generate_interesting_code(
    context: dict,
    explore_reason: str,
    result_str: str,
    user_question: str = "",
    tracker: Optional[CostTracker] = None,
    api_key: str = None,
) -> tuple[str, str]:
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
        api_key=api_key,
    )
    return parse_code_response(raw)


def reprompt_code(
    context: dict,
    broken_code: str,
    error: str,
    tracker: Optional[CostTracker] = None,
    stage: str = "reprompt_code",
    api_key: str = None,
) -> str:
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
        api_key=api_key,
    )
    _, code = parse_code_response(f"EXPLORE: fix\n{raw}")
    return code