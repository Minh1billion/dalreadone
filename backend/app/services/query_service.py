"""
query_service.py

Main query pipeline. Wires the cost tracker through every LLM call
and returns a cost_report in the response so callers can measure savings.

Optimisations active in this version:
  - max_tokens ceiling per stage (in llm_engine.py)
  - prompt field truncation (in llm_engine.py)
  - pass-2 skip when pass-1 result is too short (heuristic in llm_engine.py)
  - tracker records every call OR skip so the full picture is visible
"""

import traceback

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import File, Project
from app.storage.s3_client import get_file_bytes
from app.llm.context_builder import build_dataframe_context
from app.llm.cost_tracker import CostTracker
from app.llm.llm_engine import (
    INTERESTING_MIN_CHARS,
    generate_code,
    generate_interesting_code,
    generate_insights,
    reprompt_code,
)
from app.sandbox.code_executor import run_with_retry


def _make_reprompt_fn(context: dict, tracker: CostTracker):
    """
    Returns a closure used by run_with_retry on each failed exec attempt.
    The attempt counter in the stage name (reprompt_code#1, #2 ...) lets
    the tracker show exactly how many retries happened.
    """
    attempt_box = [0]

    def reprompt_fn(broken_code: str, error: str) -> str:
        attempt_box[0] += 1
        print(f"[REPROMPT attempt {attempt_box[0]}]\nERROR: {error}\nCODE:\n{broken_code}\n")
        stage = f"reprompt_code#{attempt_box[0]}"
        return reprompt_code(context, broken_code, error, tracker=tracker, stage=stage)

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

    Pass 1 — multi-angle exploration, returns result + up to 3 charts.
    Pass 2 — dig into anomalies; skipped when pass-1 result is trivially short.

    Response shape:
      {
        user_question        : str | None,
        explore_reason       : str,
        result               : str,
        charts               : list[dict],
        interesting_reason   : str | None,
        interesting_result   : str | None,
        interesting_charts   : list[dict],
        insight              : str,
        code                 : str,
        cost_report          : dict,
      }
    """
    tracker = CostTracker()

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

        # --- Pass 1: standard multi-angle exploration ---
        explore_reason, code = generate_code(
            context,
            user_question=user_question,
            tracker=tracker,
        )

        result_str, charts, final_code = run_with_retry(
            code=code,
            df=context["df"],
            reprompt_fn=_make_reprompt_fn(context, tracker),
        )

        # --- Pass 2: anomaly / interesting findings ---
        interesting_reason      = ""
        interesting_result_str  = ""
        interesting_charts: list[dict] = []

        int_reason, int_code = generate_interesting_code(
            context=context,
            explore_reason=explore_reason,
            result_str=result_str,
            user_question=user_question,
            tracker=tracker,
        )

        if not int_reason and not int_code:
            tracker.record_skip(
                stage="find_interesting",
                reason=f"pass-1 result too short ({len(result_str)} < {INTERESTING_MIN_CHARS} chars)",
            )
        else:
            try:
                is_empty = int_code.strip() in ("result = {}", "result={}")
                if not is_empty:
                    interesting_result_str, interesting_charts, _ = run_with_retry(
                        code=int_code,
                        df=context["df"],
                        reprompt_fn=_make_reprompt_fn(context, tracker),
                    )
                    interesting_reason = int_reason
            except Exception:
                traceback.print_exc()

        # --- Insights: combine both passes into plain-text ---
        insight = generate_insights(
            filename=record.filename,
            explore_reason=explore_reason,
            result=result_str,
            user_question=user_question,
            interesting_reason=interesting_reason,
            interesting_result=interesting_result_str,
            tracker=tracker,
        )

        sep = "=" * 60
        print(f"\n{sep}")
        print(tracker.summary())
        print(f"{sep}\n")

        return {
            "user_question":       user_question or None,
            "explore_reason":      explore_reason,
            "result":              result_str,
            "charts":              charts,
            "interesting_reason":  interesting_reason or None,
            "interesting_result":  interesting_result_str or None,
            "interesting_charts":  interesting_charts,
            "insight":             insight,
            "code":                final_code,
            "cost_report":         tracker.report(),
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))