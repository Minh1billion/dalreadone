import logging

from sqlalchemy.orm import Session

from app.llm.cost_tracker import CostTracker
from app.llm.context_builder import build_dataframe_context
from app.llm.engine import structured as structured_engine
from app.llm.engine import nlp as nlp_engine
from app.llm.insights import generate_insights
from app.sandbox.code_executor import run_with_retry
from app.services.file_service import get_file_bytes
from app.services import settings_service

logger = logging.getLogger(__name__)


def _run(engine, code, df, context, extra_globals, tracker, api_key=None):
    """Execute code with retry, using the correct engine for reprompting."""
    return run_with_retry(
        code=code,
        df=df,
        reprompt_fn=lambda broken, err: engine.reprompt_code(
            context, broken, err, tracker=tracker, api_key=api_key
        ),
        extra_globals=extra_globals,
    )


def _nlp_features_valid(nlp_features: dict) -> bool:
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
    stopwords_config: dict | None = None,
) -> dict:
    tracker  = CostTracker()
    api_key  = settings_service.get_api_key(db, user_id)

    logger.info(
        "run_query file_id=%s user_id=%s using_own_key=%s question=%r stopwords=%r",
        file_id, user_id, api_key is not None, user_question or "(none)", stopwords_config,
    )

    file_bytes, filename = get_file_bytes(db, file_id=file_id, user_id=user_id)
    context = build_dataframe_context(
        file_bytes, filename,
        stopwords_config=stopwords_config,
    )

    df      = context["df"]

    raw_nlp_features = context.get("nlp_features", {})
    is_nlp = context.get("is_nlp") and _nlp_features_valid(raw_nlp_features)

    engine        = nlp_engine if is_nlp else structured_engine
    extra_globals = {"nlp_features": raw_nlp_features} if is_nlp else None
    q             = user_question or ""

    logger.info("engine=%s  is_nlp=%s", "nlp" if is_nlp else "structured", is_nlp)

    # Pass-1
    explore_reason, code = engine.generate_code(
        context, user_question=q, tracker=tracker, api_key=api_key
    )
    logger.debug("pass1 generated code:\n%s", code)

    try:
        result_str, charts, code = _run(
            engine, code, df, context, extra_globals, tracker, api_key=api_key
        )
    except RuntimeError as exc:
        logger.error("pass1 failed after all retries:\n%s", exc)
        raise

    # Pass-2
    interesting_reason, i_code = engine.generate_interesting_code(
        context, explore_reason=explore_reason, result_str=result_str,
        user_question=q, tracker=tracker, api_key=api_key,
    )

    i_result, i_charts = None, []
    if i_code:
        logger.debug("pass2 generated code:\n%s", i_code)
        try:
            i_result, i_charts, _ = _run(
                engine, i_code, df, context, extra_globals, tracker, api_key=api_key
            )
        except RuntimeError as exc:
            logger.warning("pass2 failed (non-fatal):\n%s", exc)

    insight = generate_insights(
        filename=filename,
        explore_reason=explore_reason,
        result=result_str,
        user_question=q,
        interesting_reason=interesting_reason or "",
        interesting_result=i_result or "",
        tracker=tracker,
        api_key=api_key,
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