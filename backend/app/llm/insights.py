"""
insights.py

Shared insight generation step used by both the structured and NLP pipelines.
"""

from typing import Optional

from app.llm.cost_tracker import CostTracker
from app.llm.engine.base import invoke, truncate, MAX_RESULT_CHARS


def generate_insights(
    filename: str,
    explore_reason: str,
    result: str,
    user_question: str = "",
    interesting_reason: str = "",
    interesting_result: str = "",
    tracker: Optional[CostTracker] = None,
    schema: str = "",
    existing_chart_titles: str = "",
    api_key: str | None = None,
) -> str:
    return invoke(
        "generate_insights.txt",
        {
            "filename":              filename,
            "explore_reason":        explore_reason,
            "result":                truncate(result, MAX_RESULT_CHARS),
            "user_question":         user_question or "No specific question provided.",
            "interesting_reason":    interesting_reason or "None.",
            "interesting_result":    (
                truncate(interesting_result, MAX_RESULT_CHARS)
                if interesting_result else "None."
            ),
            "schema":                schema or "",
            "existing_chart_titles": existing_chart_titles or "none",
        },
        stage="generate_insights",
        tracker=tracker,
        api_key=api_key,
    )