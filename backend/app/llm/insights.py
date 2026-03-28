"""
insights.py

Shared insight generation step used by both the structured and NLP pipelines.

generate_insights() is pipeline-agnostic: it receives already-serialized
result strings from whichever pipeline ran, so the prompt template and
LLM call are identical regardless of data type.
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
) -> str:
    """
    Generate a plain-text insight summary combining pass-1 and pass-2 results.

    Args:
        filename           : Original file name shown to the LLM for context.
        explore_reason     : One-line description of what pass-1 analysed.
        result             : Serialized pass-1 result string.
        user_question      : Original user question (empty if auto-explore).
        interesting_reason : One-line description of what pass-2 found (optional).
        interesting_result : Serialized pass-2 result string (optional).
        tracker            : Cost tracker instance (optional).

    Returns:
        Plain-text insight paragraph(s).
    """
    return invoke(
        "generate_insights.txt",
        {
            "filename":           filename,
            "explore_reason":     explore_reason,
            "result":             truncate(result, MAX_RESULT_CHARS),
            "user_question":      user_question or "No specific question provided.",
            "interesting_reason": interesting_reason or "None.",
            "interesting_result": (
                truncate(interesting_result, MAX_RESULT_CHARS)
                if interesting_result else "None."
            ),
        },
        stage="generate_insights",
        tracker=tracker,
    )