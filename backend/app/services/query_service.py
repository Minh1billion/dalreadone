"""
services/query_service.py
"""

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

    engine       = nlp_engine if context.get("is_nlp") else structured_engine
    extra_globals = {"nlp_features": context["nlp_features"]} if context.get("is_nlp") else None
    q            = user_question or ""

    # Pass-1
    explore_reason, code       = engine.generate_code(context, user_question=q, tracker=tracker)
    result_str, charts, code   = _run(engine, code, df, context, extra_globals, tracker)

    # Pass-2
    interesting_reason, i_code = engine.generate_interesting_code(
        context, explore_reason=explore_reason, result_str=result_str,
        user_question=q, tracker=tracker,
    )
    i_result, i_charts, _      = _run(engine, i_code, df, context, extra_globals, tracker) \
                                  if i_code else (None, [], None)

    # Insight
    insight = generate_insights(
        filename=filename,
        explore_reason=explore_reason,
        result=result_str,
        user_question=q,
        interesting_reason=interesting_reason or "",
        interesting_result=i_result or "",
        tracker=tracker,
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