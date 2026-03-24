from pathlib import Path
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from app.core.config import Config

TEMPLATE_DIR = Path(__file__).parent / "template"

_llm = ChatGroq(
    model=Config.MODEL_ID,
    api_key=Config.GROQ_API_KEY,
    temperature=0.2,
)


def _load_template(filename: str) -> PromptTemplate:
    text = (TEMPLATE_DIR / filename).read_text()
    return PromptTemplate.from_template(text)


def _invoke(template_file: str, variables: dict) -> str:
    prompt = _load_template(template_file)
    chain = prompt | _llm
    response = chain.invoke(variables)
    return response.content.strip()


def generate_code(context: dict, user_question: str = "") -> tuple[str, str]:
    """
    LLM decides what to explore and generates pandas code returning a dict result.
    Returns: (explore_reason, pandas_code)
    """
    raw = _invoke("generate_code.txt", {
        "filename": context["filename"],
        "schema": context["schema"],
        "sample_rows": context["sample_rows"],
        "stats": context["stats"],
        "user_question": user_question or "No specific question — explore freely.",
    })
    return _parse_code_response(raw)


def reprompt_code(context: dict, broken_code: str, error: str) -> str:
    """
    Ask LLM to fix broken code given the error message.
    Returns: fixed pandas code string
    """
    raw = _invoke("fix_code.txt", {
        "filename": context["filename"],
        "schema": context["schema"],
        "broken_code": broken_code,
        "error": error,
    })
    _, code = _parse_code_response(f"EXPLORE: fix\n{raw}")
    return code


def generate_insights(
    filename: str,
    explore_reason: str,
    result: str,
    user_question: str = "",
) -> str:
    """Generate plain-text insight from multi-section result."""
    return _invoke("generate_insights.txt", {
        "filename": filename,
        "explore_reason": explore_reason,
        "result": result,
        "user_question": user_question or "No specific question provided.",
    })


def _parse_code_response(raw: str) -> tuple[str, str]:
    """Parse EXPLORE / CODE block from LLM response."""
    explore_reason = ""
    code_lines = []
    in_code_block = False

    for line in raw.splitlines():
        if line.startswith("EXPLORE:"):
            explore_reason = line.replace("EXPLORE:", "").strip()
        elif line.strip() == "```python":
            in_code_block = True
        elif line.strip() == "```" and in_code_block:
            in_code_block = False
        elif in_code_block:
            code_lines.append(line)

    code = "\n".join(code_lines).strip()

    if not code:
        raise ValueError(f"Could not parse code from LLM response:\n{raw}")

    return explore_reason, code