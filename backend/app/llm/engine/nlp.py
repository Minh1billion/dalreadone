"""
engine/nlp.py

LLM call wrappers for the NLP (text-heavy) pipeline.

Pre-computed features from nlp_features.py are serialized into a
compact human-readable string before being injected into the prompt,
so the LLM can reference real numbers instead of guessing.
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


# Feature serializer
def _format_nlp_features(nlp_features: dict) -> str:
    """
    Serialize pre-computed NLP features into a compact,
    human-readable block for inclusion in the LLM prompt.

    Keeps only the top-10 keywords and top-3 keywords per cluster
    to avoid bloating the prompt.
    """
    lines = []
    for col, feats in nlp_features.items():
        sent    = feats["sentiment"]
        kws     = ", ".join(f"{w}({s:.2f})" for w, s in feats["keywords"][:10])
        clusters = "; ".join(
            f'{c["topic"]}:[{", ".join(c["keywords"][:3])}]'
            for c in feats["topic_clusters"]
        )
        dist = feats["length_distribution"]
        lines.append(
            f"[{col}]\n"
            f"  sentiment : mean={sent['mean']:.3f}, "
            f"pos={sent['positive_pct']:.1f}%, "
            f"neg={sent['negative_pct']:.1f}%, "
            f"neu={sent['neutral_pct']:.1f}%\n"
            f"  keywords  : {kws}\n"
            f"  clusters  : {clusters}\n"
            f"  length    : short={dist['short']:.1f}%, "
            f"medium={dist['medium']:.1f}%, "
            f"long={dist['long']:.1f}%, "
            f"very_long={dist['very_long']:.1f}%"
        )
    return "\n\n".join(lines)



# Public API
def generate_code(
    context: dict,
    user_question: str = "",
    tracker: Optional[CostTracker] = None,
) -> tuple[str, str]:
    """
    Pass-1: generate exploratory analysis code for a text-heavy dataset.

    Returns:
        (explore_reason, python_code)
    """
    raw = invoke(
        "generate_code_nlp.txt",
        {
            "filename":      context["filename"],
            "schema":        truncate(context["schema"],      MAX_SCHEMA_CHARS),
            "sample_rows":   truncate(context["sample_rows"], MAX_SAMPLE_ROWS_CHARS),
            "stats":         truncate(context["stats"],       MAX_STATS_CHARS),
            "nlp_features":  truncate(
                                _format_nlp_features(context.get("nlp_features", {})),
                                MAX_STATS_CHARS,
                             ),
            "user_question": user_question or "No specific question — explore freely.",
        },
        stage="generate_code_nlp",
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
    Pass-2: generate code to surface anomalies in a text-heavy dataset.
    Returns ("", "") if pass-1 result is too short to be worth a second pass.

    Returns:
        (interesting_reason, python_code)
    """
    if len(result_str) < INTERESTING_MIN_CHARS:
        return "", ""

    raw = invoke(
        "find_interesting_nlp.txt",
        {
            "filename":       context["filename"],
            "schema":         truncate(context["schema"],     MAX_SCHEMA_CHARS),
            "explore_reason": explore_reason,
            "result":         truncate(result_str,            MAX_RESULT_CHARS),
            "nlp_features":   truncate(
                                _format_nlp_features(context.get("nlp_features", {})),
                                MAX_STATS_CHARS,
                              ),
            "user_question":  user_question or "No specific question provided.",
        },
        stage="find_interesting_nlp",
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
    Ask the LLM to fix broken code from the NLP pipeline.
    Reuses the same fix_code.txt template as the structured pipeline
    since the repair task is identical.

    Returns:
        Fixed python_code string.
    """
    from app.llm.engine.structured import reprompt_code as _reprompt
    return _reprompt(context, broken_code, error, tracker=tracker, stage=stage)