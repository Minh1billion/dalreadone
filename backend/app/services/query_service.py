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

    Response shape:
      {
        user_question: str | None,
        explore_reason: str,
        result: str,
        charts: list[dict],          # replaces old chart_data (single dict)
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

        # Pass 2: look for interesting/anomalous findings
        interesting_reason = ""
        interesting_result_str = ""
        interesting_charts: list[dict] = []

        try:
            int_reason, int_code = generate_interesting_code(
                context=context,
                explore_reason=explore_reason,
                result_str=result_str,
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
            result=result_str,
            user_question=user_question,
            interesting_reason=interesting_reason,
            interesting_result=interesting_result_str,
        )

        return {
            "user_question": user_question or None,
            "explore_reason": explore_reason,
            "result": result_str,
            "charts": charts,                              # list of chart dicts
            "interesting_reason": interesting_reason or None,
            "interesting_result": interesting_result_str or None,
            "interesting_charts": interesting_charts,      # list of chart dicts
            "insight": insight,
            "code": final_code,
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))