from sqlalchemy.orm import Session
from fastapi import HTTPException
import traceback

from app.models import File, Project
from app.storage.s3_client import get_file_bytes
from app.llm.context_builder import build_dataframe_context
from app.llm.llm_engine import (
    generate_code,
    generate_interesting_code,
    generate_insights,
    reprompt_code,
)
from app.sandbox.code_executor import run_with_retry

# Max characters of a result string fed back into a subsequent LLM prompt.
# ~4 chars per token → 3,200 chars ≈ 800 tokens.
# The full result is still returned to the caller unchanged.
_MAX_RESULT_CHARS_FOR_LLM = 3200

# Max characters of the interesting_result fed into generate_insights.
# Pass-2 results are usually shorter, but cap them anyway.
_MAX_INTERESTING_CHARS_FOR_LLM = 1600


def _trim(text: str, limit: int) -> str:
    """Hard-truncate text to limit chars, appending a marker when cut."""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... [truncated for brevity]"


def _make_reprompt_fn(context: dict):
    def reprompt_fn(broken_code: str, error: str) -> str:
        return reprompt_code(context, broken_code, error)
    return reprompt_fn


def run_query(
    db: Session,
    project_id: int,
    file_id: int,
    user_id: int,
    user_question: str = "",
) -> dict:
    """
    Main query pipeline.

    Pass 1: multi-angle exploration, returns result + up to 3 charts.
    Pass 2: look for interesting/anomalous findings, also returns charts.

    Token-saving measures applied here:
      - result_str is truncated before being fed into pass-2 and insights prompts.
        The full string is still returned to the API caller.
      - interesting_result_str is also truncated before insights.

    Response shape:
      {
        user_question: str | None,
        explore_reason: str,
        result: str,
        charts: list[dict],
        interesting_reason: str | None,
        interesting_result: str | None,
        interesting_charts: list[dict],
        insight: str,
        code: str,
      }
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        record = db.query(File).filter(
            File.id == file_id,
            File.project_id == project_id,
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="File not found")

        file_bytes = get_file_bytes(record.s3_key)
        context = build_dataframe_context(file_bytes, record.filename)

        # Pass 1: standard multi-angle exploration
        explore_reason, code = generate_code(context, user_question=user_question)

        result_str, charts, final_code = run_with_retry(
            code=code,
            df=context["df"],
            reprompt_fn=_make_reprompt_fn(context),
        )

        # Trimmed version used only as LLM input - full result_str returned to caller
        result_str_trimmed = _trim(result_str, _MAX_RESULT_CHARS_FOR_LLM)

        # Pass 2: look for interesting/anomalous findings
        interesting_reason = ""
        interesting_result_str = ""
        interesting_charts: list[dict] = []

        try:
            int_reason, int_code = generate_interesting_code(
                context=context,
                explore_reason=explore_reason,
                result_str=result_str_trimmed,   # trimmed - saves ~800 tokens/call
                user_question=user_question,
            )

            is_empty = int_code.strip() in ("result = {}", "result={}")
            if not is_empty:
                interesting_result_str, interesting_charts, _ = run_with_retry(
                    code=int_code,
                    df=context["df"],
                    reprompt_fn=_make_reprompt_fn(context),
                )
                interesting_reason = int_reason

        except Exception:
            traceback.print_exc()

        # Generate final insights combining both passes
        insight = generate_insights(
            filename=record.filename,
            explore_reason=explore_reason,
            result=result_str_trimmed,           # trimmed - saves ~800 tokens/call
            user_question=user_question,
            interesting_reason=interesting_reason,
            interesting_result=_trim(           # trimmed - saves up to ~400 tokens
                interesting_result_str,
                _MAX_INTERESTING_CHARS_FOR_LLM,
            ),
        )

        return {
            "user_question": user_question or None,
            "explore_reason": explore_reason,
            "result": result_str,               # full, untruncated
            "charts": charts,
            "interesting_reason": interesting_reason or None,
            "interesting_result": interesting_result_str or None,  # full
            "interesting_charts": interesting_charts,
            "insight": insight,
            "code": final_code,
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))