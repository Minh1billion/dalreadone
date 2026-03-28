"""
engine/base.py

Core LLM invocation layer.
Handles model instantiation, prompt loading, rate-limit retries,
token tracking, and prompt-field truncation.

All higher-level engine modules (structured, nlp) build on top of this.
"""

import re
import time
from pathlib import Path
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

from app.core.config import Config
from app.llm.cost_tracker import CostTracker


# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "template"


# Per-stage token budgets
# Keeps costs predictable; raise only if output quality suffers.
STAGE_MAX_TOKENS: dict[str, int] = {
    "generate_code":          900,
    "generate_code_nlp":      900,
    "find_interesting":       900,
    "find_interesting_nlp":   900,
    "reprompt_code":          700,
    "generate_insights":      500,
}


# Prompt field truncation limits (characters)
MAX_SCHEMA_CHARS      = 3_000
MAX_SAMPLE_ROWS_CHARS = 2_000
MAX_STATS_CHARS       = 2_000
MAX_RESULT_CHARS      = 4_000


# Pass-2 skip heuristic
# If pass-1 result is shorter than this, skip find_interesting entirely.
INTERESTING_MIN_CHARS = 200


# Rate-limit retry config
_RATE_LIMIT_MAX_RETRIES = 4
_RATE_LIMIT_BASE_DELAY  = 1.0       # seconds, doubles each attempt
_MAX_WAIT_SECONDS       = 30.0
_RETRY_AFTER_RE = re.compile(r"try again in (\d+)m([\d.]+)s", re.IGNORECASE)



# Internal helpers
def _make_llm(stage: str) -> ChatGroq:
    """Instantiate a ChatGroq model with the token budget for this stage."""
    base_stage = stage.split("#")[0]   # strip retry suffix e.g. "reprompt_code#1"
    return ChatGroq(
        model=Config.MODEL_ID,
        api_key=Config.GROQ_API_KEY,
        temperature=0.2,
        max_tokens=STAGE_MAX_TOKENS.get(base_stage, 900),
    )


def _load_template(filename: str) -> PromptTemplate:
    text = (TEMPLATE_DIR / filename).read_text()
    return PromptTemplate.from_template(text)


def truncate(text: str, max_chars: int) -> str:
    """Hard-truncate a string and append a notice if truncation occurred."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n... [truncated to {max_chars} chars]"


def _extract_token_counts(response) -> tuple[int, int]:
    """Extract (prompt_tokens, completion_tokens) from a LangChain response."""
    meta = getattr(response, "usage_metadata", None)
    if isinstance(meta, dict):
        inp = meta.get("input_tokens", 0)
        out = meta.get("output_tokens", 0)
        if inp or out:
            return int(inp), int(out)

    rmeta = getattr(response, "response_metadata", None)
    if isinstance(rmeta, dict):
        usage = rmeta.get("token_usage") or {}
        inp = usage.get("prompt_tokens", 0)
        out = usage.get("completion_tokens", 0)
        if inp or out:
            return int(inp), int(out)

    # Fallback: estimate from character count
    out_chars = len(getattr(response, "content", "") or "")
    return 0, max(1, out_chars // 4)


def _parse_retry_after(message: str) -> float | None:
    """Parse 'try again in Xm Y.Zs' from a rate-limit error message."""
    m = _RETRY_AFTER_RE.search(message)
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    return None



# Public invocation API


def invoke_with_retry(
    chain,
    variables: dict,
    stage: str,
    tracker: Optional[CostTracker] = None,
) -> str:
    """
    Invoke a LangChain chain with automatic rate-limit retries.

    Exponential back-off up to _MAX_WAIT_SECONDS.
    Raises immediately if the suggested wait exceeds the cap.
    """
    delay = _RATE_LIMIT_BASE_DELAY

    for attempt in range(1, _RATE_LIMIT_MAX_RETRIES + 1):
        t0 = time.monotonic()
        try:
            response   = chain.invoke(variables)
            latency_ms = int((time.monotonic() - t0) * 1000)

            if tracker is not None:
                record_stage = stage if attempt == 1 else f"{stage}#retry{attempt - 1}"
                prompt_tokens, completion_tokens = _extract_token_counts(response)
                tracker.record(
                    stage=record_stage,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    latency_ms=latency_ms,
                )

            return response.content.strip()

        except Exception as e:
            error_str = str(e)
            is_rate_limit = (
                "429"                in error_str
                or "rate_limit_exceeded" in error_str
                or "Rate limit"          in error_str
            )

            if not is_rate_limit or attempt == _RATE_LIMIT_MAX_RETRIES:
                raise

            suggested = _parse_retry_after(error_str)
            if suggested is not None and suggested > _MAX_WAIT_SECONDS:
                print(
                    f"[engine] Rate limit wait too long "
                    f"({suggested:.0f}s > {_MAX_WAIT_SECONDS:.0f}s cap) — raising."
                )
                raise

            wait = min(suggested or delay, _MAX_WAIT_SECONDS)
            print(
                f"[engine] Rate limit (attempt {attempt}/{_RATE_LIMIT_MAX_RETRIES}). "
                f"Waiting {wait:.1f}s..."
            )
            time.sleep(wait)
            delay *= 2


def invoke(
    template_file: str,
    variables: dict,
    stage: str,
    tracker: Optional[CostTracker] = None,
) -> str:
    """Load a template, build the chain, and invoke with retry."""
    prompt = _load_template(template_file)
    llm    = _make_llm(stage)
    chain  = prompt | llm
    return invoke_with_retry(chain, variables, stage=stage, tracker=tracker)


def parse_code_response(raw: str) -> tuple[str, str]:
    """
    Parse the LLM response into (explore_reason, code).

    Expected format:
        EXPLORE: <one-line reason>
        ```python
        <code>
        ```
    """
    explore_reason = ""
    code_lines     = []
    in_code_block  = False

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