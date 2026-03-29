from sqlalchemy.orm import Session

from app.llm.cost_tracker import CostTracker
from app.llm.context_builder import build_dataframe_context
from app.llm.engine import structured as structured_engine
from app.llm.engine import nlp as nlp_engine
from app.llm.insights import generate_insights
from app.sandbox.code_executor import run_with_retry
from app.services.file_service import get_file_bytes


def _run(engine, code, df, context, extra_globals, tracker):
    """Execute code with retry, using the correct engine for reprompting."""
    return run_with_retry(
        code=code,
        df=df,
        reprompt_fn=lambda broken, err: engine.reprompt_code(
            context, broken, err, tracker=tracker
        ),
        extra_globals=extra_globals,
    )


def _nlp_features_valid(nlp_features: dict) -> bool:
    """
    Return True only when every column in nlp_features has a fully-formed
    sentiment sub-dict (the key accessed most often in LLM-generated code).

    This guards against two failure modes:
        1. compute_nlp_features raised before building any entry  → empty dict
        2. A column's sub-extractor failed and returned a partial dict
           (shouldn't happen after the features.py fix, but cheap to check)
    """
    if not nlp_features:
        return False
    for col, feats in nlp_features.items():
        sent = feats.get("sentiment")
        if not isinstance(sent, dict):
            return False
        for key in ("scores", "mean", "positive_pct", "negative_pct", "neutral_pct"):
            if key not in sent:
                return False
    return True


def run_query(
    db: Session,
    project_id: int,
    file_id: int,
    user_id: int,
    user_question: str = "",
) -> dict:
    tracker = CostTracker()

    file_bytes, filename = get_file_bytes(db, file_id=file_id, user_id=user_id)
    context = build_dataframe_context(file_bytes, filename)
    df      = context["df"]

    # Validate nlp_features before deciding which engine to use.
    # If the features are missing or malformed we fall back to the structured
    # engine so the query still succeeds instead of raising a sandbox KeyError.
    raw_nlp_features = context.get("nlp_features", {})
    is_nlp = context.get("is_nlp") and _nlp_features_valid(raw_nlp_features)

    engine        = nlp_engine if is_nlp else structured_engine
    extra_globals = {"nlp_features": raw_nlp_features} if is_nlp else None
    q             = user_question or ""

    # Pass-1
    explore_reason, code     = engine.generate_code(context, user_question=q, tracker=tracker)
    result_str, charts, code = _run(engine, code, df, context, extra_globals, tracker)

    # Pass-2
    interesting_reason, i_code = engine.generate_interesting_code(
        context, explore_reason=explore_reason, result_str=result_str,
        user_question=q, tracker=tracker,
    )
    i_result, i_charts, _ = (
        _run(engine, i_code, df, context, extra_globals, tracker)
        if i_code else (None, [], None)
    )

    # Insight — pass schema and chart titles for template compatibility
    insight = generate_insights(
        filename=filename,
        explore_reason=explore_reason,
        result=result_str,
        user_question=q,
        interesting_reason=interesting_reason or "",
        interesting_result=i_result or "",
        tracker=tracker,
        schema=context.get("schema", ""),
        existing_chart_titles=", ".join(
            f'"{c["title"]}"' for c in charts if isinstance(c, dict) and "title" in c
        ),
    )

    return {
        "user_question":      q or None,
        "explore_reason":     explore_reason,
        "result":             result_str,
        "charts":             charts,
        "interesting_reason": interesting_reason or None,
        "interesting_result": i_result,
        "interesting_charts": i_charts,
        "insight":            insight,
        "code":               code,
        "cost_report":        tracker.report(),
    }