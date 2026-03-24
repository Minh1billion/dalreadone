from sqlalchemy.orm import Session
from fastapi import HTTPException

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
) -> dict:
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

    # 2.2 Fetch file from S3 and build dataframe context
    file_bytes = get_file_bytes(record.s3_key)
    context = build_dataframe_context(file_bytes, record.filename)

    # 2.3 Generate pandas code from LLM
    explore_reason, code = generate_code(context)

    # 2.5 + 2.6 + 2.7b Execute code with retry on failure
    result_str, final_code = run_with_retry(
        code=code,
        df=context["df"],
        reprompt_fn=_make_reprompt_fn(context),
    )

    # 2.9 Generate plain-text insight from result
    insight = generate_insights(record.filename, explore_reason, result_str)

    return {
        "explore_reason": explore_reason,
        "result": result_str,
        "insight": insight,
        "code": final_code,
    }