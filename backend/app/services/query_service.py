from sqlalchemy.orm import Session
from fastapi import HTTPException
import traceback

from app.models import File, Project
from app.storage.s3_client import get_file_bytes
from app.llm.context_builder import build_dataframe_context
from app.llm.llm_engine import generate_code, generate_insights, reprompt_code
from app.sandbox.code_executor import run_with_retry


def _make_reprompt_fn(context: dict):
    """Closure passed to run_with_retry. Signature: (broken_code, error) -> fixed_code"""
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
    try:
        # Verify project exists and belongs to user
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Verify file exists and belongs to project
        record = db.query(File).filter(
            File.id == file_id,
            File.project_id == project_id,
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="File not found")

        # Fetch file from S3 and build dataframe context
        file_bytes = get_file_bytes(record.s3_key)
        context = build_dataframe_context(file_bytes, record.filename)

        # Generate multi-explore pandas code from LLM
        explore_reason, code = generate_code(context, user_question=user_question)

        # Execute code with retry on failure
        result_str, final_code = run_with_retry(
            code=code,
            df=context["df"],
            reprompt_fn=_make_reprompt_fn(context),
        )

        # Generate plain-text insight from multi-section result
        insight = generate_insights(
            filename=record.filename,
            explore_reason=explore_reason,
            result=result_str,
            user_question=user_question,
        )

        return {
            "user_question": user_question or None,
            "explore_reason": explore_reason,
            "result": result_str,
            "insight": insight,
            "code": final_code,
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))