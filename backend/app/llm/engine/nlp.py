from typing import Optional

from app.llm.cost_tracker import CostTracker
from app.llm.engine.base import (
    invoke, parse_code_response, truncate,
    MAX_SCHEMA_CHARS, MAX_SAMPLE_ROWS_CHARS, MAX_STATS_CHARS,
    MAX_RESULT_CHARS, INTERESTING_MIN_CHARS,
)


def _format_nlp_features(nlp_features: dict) -> str:
    """Serialize pre-computed NLP features into a compact prompt-friendly block."""
    lines = []
    for col, feats in nlp_features.items():
        sent     = feats["sentiment"]
        kws      = ", ".join(f"{w}({s:.2f})" for w, s in feats["keywords"][:10])
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


def _extract_chart_titles(result_str: str) -> list[str]:
    """Extract chart titles from pass-1 result string to prevent pass-2 duplicates."""
    import re
    return re.findall(r'"title"\s*:\s*"([^"]+)"', result_str)


def generate_code(
    context: dict,
    user_question: str = "",
    tracker: Optional[CostTracker] = None,
    api_key: str = None,
) -> tuple[str, str]:
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
            "user_question": user_question or "No specific question - explore freely.",
        },
        stage="generate_code_nlp",
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

    existing_titles     = _extract_chart_titles(result_str)
    existing_titles_str = ", ".join(f'"{t}"' for t in existing_titles) if existing_titles else "none"

    raw = invoke(
        "find_interesting_nlp.txt",
        {
            "filename":              context["filename"],
            "schema":                truncate(context["schema"],     MAX_SCHEMA_CHARS),
            "explore_reason":        explore_reason,
            "result":                truncate(result_str,            MAX_RESULT_CHARS),
            "nlp_features":          truncate(
                                       _format_nlp_features(context.get("nlp_features", {})),
                                       MAX_STATS_CHARS,
                                     ),
            "user_question":         user_question or "No specific question provided.",
            "existing_chart_titles": existing_titles_str,
        },
        stage="find_interesting_nlp",
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
    from app.llm.engine.structured import reprompt_code as _reprompt
    return _reprompt(context, broken_code, error, tracker=tracker, stage=stage, api_key=api_key)