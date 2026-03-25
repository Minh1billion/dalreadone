import time
import re
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

# How many times to retry on rate-limit (429) before giving up
_RATE_LIMIT_MAX_RETRIES = 4

# Seconds to wait between retries — doubles each attempt (1, 2, 4, 8...)
_RATE_LIMIT_BASE_DELAY = 1.0

# Hard cap on a single sleep inside the server request handler.
_MAX_WAIT_SECONDS = 30.0

# Regex to extract "retry after NmSs" from the Groq error message
_RETRY_AFTER_RE = re.compile(r"try again in (\d+)m([\d.]+)s", re.IGNORECASE)


def _parse_retry_after(message: str) -> float | None:
    """
    Parse the wait time from a Groq 429 error message.
    Returns seconds as float, or None if not found.

    Example message fragment:
      'Please try again in 2m57.12s.'
    """
    m = _RETRY_AFTER_RE.search(message)
    if m:
        minutes = int(m.group(1))
        seconds = float(m.group(2))
        return minutes * 60 + seconds
    return None


def _invoke_with_retry(chain, variables: dict) -> str:
    """
    Invoke a LangChain chain, retrying up to _RATE_LIMIT_MAX_RETRIES times
    if Groq returns a 429 rate-limit error.

    Wait strategy (in order of priority):
      1. Parse the 'retry after' seconds from the error message.
         If that value exceeds _MAX_WAIT_SECONDS, raise immediately —
         sleeping too long inside a server handler causes client timeout.
      2. Otherwise fall back to exponential backoff capped at _MAX_WAIT_SECONDS.
    """
    delay = _RATE_LIMIT_BASE_DELAY

    for attempt in range(1, _RATE_LIMIT_MAX_RETRIES + 1):
        try:
            response = chain.invoke(variables)
            return response.content.strip()

        except Exception as e:
            error_str = str(e)

            # Only retry on rate-limit errors
            is_rate_limit = (
                "429" in error_str
                or "rate_limit_exceeded" in error_str
                or "Rate limit" in error_str
            )

            if not is_rate_limit or attempt == _RATE_LIMIT_MAX_RETRIES:
                raise

            suggested = _parse_retry_after(error_str)

            # If Groq says to wait longer than our cap, give up now so the
            # HTTP response reaches the client before it times out.
            if suggested is not None and suggested > _MAX_WAIT_SECONDS:
                print(
                    f"[llm_engine] Rate limit wait too long ({suggested:.0f}s > "
                    f"{_MAX_WAIT_SECONDS:.0f}s cap) — raising immediately."
                )
                raise

            wait = min(suggested or delay, _MAX_WAIT_SECONDS)
            print(
                f"[llm_engine] Rate limit hit (attempt {attempt}/{_RATE_LIMIT_MAX_RETRIES}). "
                f"Waiting {wait:.1f}s before retry..."
            )
            time.sleep(wait)
            delay *= 2  # exponential backoff for subsequent fallback waits


def _load_template(filename: str) -> PromptTemplate:
    text = (TEMPLATE_DIR / filename).read_text()
    return PromptTemplate.from_template(text)


def _invoke(template_file: str, variables: dict) -> str:
    prompt = _load_template(template_file)
    chain = prompt | _llm
    return _invoke_with_retry(chain, variables)


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


def generate_interesting_code(
    context: dict,
    explore_reason: str,
    result_str: str,
    user_question: str = "",
) -> tuple[str, str]:
    """
    Second-pass: LLM looks at first-pass results and decides if there's
    anything interesting worth digging into. Returns empty code if nothing notable.
    Returns: (interesting_reason, pandas_code)
    """
    raw = _invoke("find_interesting.txt", {
        "filename": context["filename"],
        "schema": context["schema"],
        "explore_reason": explore_reason,
        "result": result_str,
        "user_question": user_question or "No specific question provided.",
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
    interesting_reason: str = "",
    interesting_result: str = "",
) -> str:
    """Generate plain-text insight from multi-section result."""
    return _invoke("generate_insights.txt", {
        "filename": filename,
        "explore_reason": explore_reason,
        "result": result,
        "user_question": user_question or "No specific question provided.",
        "interesting_reason": interesting_reason or "None.",
        "interesting_result": interesting_result or "None.",
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