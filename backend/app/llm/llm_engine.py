"""
llm_engine.py

LLM call layer with three cost optimisations applied without touching output quality:

  1. max_tokens per call
     Each stage has a tight ceiling so the model cannot ramble.
     generate_code / find_interesting need room for Python blocks (~900).
     reprompt_code only fixes code, needs less (~700).
     generate_insights is plain prose, capped at 500.

  2. Prompt truncation
     schema, sample_rows, and stats are the largest repeated inputs.
     _truncate() hard-caps them so a wide CSV with 80 columns does not
     blow up the prompt on every call.

  3. Pass-2 skip heuristic
     If pass-1 result is short (< INTERESTING_MIN_CHARS characters) the
     dataset is probably tiny or trivial. generate_interesting_code is
     skipped entirely and the caller gets back an empty reason/code so
     query_service.py can log a SKIPPED record in the cost tracker.

All public functions accept an optional CostTracker and record their own
token usage. The tracker is passed in from query_service.py so one tracker
instance spans the whole pipeline for a single user request.
"""

import time
import re
from pathlib import Path
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

from app.core.config import Config
from app.llm.cost_tracker import CostTracker

TEMPLATE_DIR = Path(__file__).parent / "template"


# Per-stage max_tokens ceilings
# Groq counts output tokens toward rate limits, so tight ceilings save quota.
_MAX_TOKENS: dict[str, int] = {
    "generate_code":       900,
    "find_interesting":    900,
    "reprompt_code":       700,
    "generate_insights":   500,
}


# Prompt input truncation limits (characters, not tokens)
# Keeps prompts from exploding on wide / long CSVs.
# Rough rule: 1 token ~ 4 chars, so 6000 chars ~ 1500 tokens per field.
_MAX_SCHEMA_CHARS      = 3_000   # ~750 tokens
_MAX_SAMPLE_ROWS_CHARS = 2_000   # ~500 tokens
_MAX_STATS_CHARS       = 2_000   # ~500 tokens
_MAX_RESULT_CHARS      = 4_000   # ~1000 tokens  (pass-2 input)

# Skip pass-2 when pass-1 result is shorter than this —
# tiny result means there is nothing interesting to dig into.
INTERESTING_MIN_CHARS = 200

# Rate-limit retry config
_RATE_LIMIT_MAX_RETRIES = 4
_RATE_LIMIT_BASE_DELAY  = 1.0
_MAX_WAIT_SECONDS       = 30.0
_RETRY_AFTER_RE = re.compile(r"try again in (\d+)m([\d.]+)s", re.IGNORECASE)


def _extract_token_counts(response) -> tuple[int, int]:
    """
    Extract (prompt_tokens, completion_tokens) from a Groq LangChain response.

    Groq can surface usage in three different places depending on the
    SDK version and endpoint — we try all of them in order:

      1. response.usage_metadata          dict  {"input_tokens": N, "output_tokens": N}
      2. response.response_metadata       dict  {"token_usage": {"prompt_tokens": N, ...}}
      3. response.additional_kwargs       dict  same nested structure as (2)

    Falls back to a character-count estimate (1 token ~ 4 chars) so the
    tracker always has something to show even if Groq changes its schema.
    """
    # attempt 1: usage_metadata — confirmed Groq format:
    #   {"input_tokens": N, "output_tokens": N, "total_tokens": N}
    meta = getattr(response, "usage_metadata", None)
    if isinstance(meta, dict):
        inp = meta.get("input_tokens", 0)
        out = meta.get("output_tokens", 0)
        if inp or out:
            return int(inp), int(out)

    # attempt 2: response_metadata.token_usage — Groq also mirrors here:
    #   {"prompt_tokens": N, "completion_tokens": N, ...}
    rmeta = getattr(response, "response_metadata", None)
    if isinstance(rmeta, dict):
        usage = rmeta.get("token_usage") or {}
        inp = usage.get("prompt_tokens", 0)
        out = usage.get("completion_tokens", 0)
        if inp or out:
            return int(inp), int(out)

    # fallback: estimate from output character count (1 token ~ 4 chars)
    out_chars = len(getattr(response, "content", "") or "")
    return 0, max(1, out_chars // 4)


def _make_llm(stage: str) -> ChatGroq:
    """Return a ChatGroq instance with the correct max_tokens for this stage."""
    return ChatGroq(
        model=Config.MODEL_ID,
        api_key=Config.GROQ_API_KEY,
        temperature=0.2,
        max_tokens=_MAX_TOKENS.get(stage, 900),
    )


def _truncate(text: str, max_chars: int) -> str:
    """
    Hard-cap a string to max_chars.
    Appends a note so the LLM knows the content was cut.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n... [truncated to {max_chars} chars]"


def _parse_retry_after(message: str) -> float | None:
    m = _RETRY_AFTER_RE.search(message)
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    return None


def _invoke_with_retry(
    chain,
    variables: dict,
    stage: str,
    tracker: Optional[CostTracker] = None,
) -> str:
    """
    Invoke a LangChain chain with exponential-backoff retry on Groq 429.
    Records token usage in the tracker when usage_metadata is available.
    """
    delay = _RATE_LIMIT_BASE_DELAY

    for attempt in range(1, _RATE_LIMIT_MAX_RETRIES + 1):
        t0 = time.monotonic()
        try:
            response = chain.invoke(variables)
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
                "429" in error_str
                or "rate_limit_exceeded" in error_str
                or "Rate limit" in error_str
            )

            if not is_rate_limit or attempt == _RATE_LIMIT_MAX_RETRIES:
                raise

            suggested = _parse_retry_after(error_str)

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
            delay *= 2


def _load_template(filename: str) -> PromptTemplate:
    text = (TEMPLATE_DIR / filename).read_text()
    return PromptTemplate.from_template(text)


def _invoke(
    template_file: str,
    variables: dict,
    stage: str,
    tracker: Optional[CostTracker] = None,
) -> str:
    prompt = _load_template(template_file)
    llm = _make_llm(stage)
    chain = prompt | llm
    return _invoke_with_retry(chain, variables, stage=stage, tracker=tracker)


# Public API
def generate_code(
    context: dict,
    user_question: str = "",
    tracker: Optional[CostTracker] = None,
) -> tuple[str, str]:
    """
    Pass 1: LLM decides what to explore and generates pandas code.
    Returns: (explore_reason, pandas_code)
    """
    raw = _invoke(
        "generate_code.txt",
        {
            "filename":    context["filename"],
            "schema":      _truncate(context["schema"],      _MAX_SCHEMA_CHARS),
            "sample_rows": _truncate(context["sample_rows"], _MAX_SAMPLE_ROWS_CHARS),
            "stats":       _truncate(context["stats"],       _MAX_STATS_CHARS),
            "user_question": user_question or "No specific question — explore freely.",
        },
        stage="generate_code",
        tracker=tracker,
    )
    return _parse_code_response(raw)


def generate_interesting_code(
    context: dict,
    explore_reason: str,
    result_str: str,
    user_question: str = "",
    tracker: Optional[CostTracker] = None,
) -> tuple[str, str]:
    """
    Pass 2: LLM looks at pass-1 results and digs into anomalies.

    Returns ("", "") when the pass-1 result is too short to be worth
    analysing — the caller should record a SKIPPED entry in the tracker
    instead of making the LLM call.

    Returns: (interesting_reason, pandas_code)
    """
    # Skip heuristic: if result is tiny, nothing interesting to find
    if len(result_str) < INTERESTING_MIN_CHARS:
        return "", ""

    raw = _invoke(
        "find_interesting.txt",
        {
            "filename":      context["filename"],
            "schema":        _truncate(context["schema"],     _MAX_SCHEMA_CHARS),
            "explore_reason": explore_reason,
            "result":        _truncate(result_str,            _MAX_RESULT_CHARS),
            "user_question": user_question or "No specific question provided.",
        },
        stage="find_interesting",
        tracker=tracker,
    )
    return _parse_code_response(raw)


def reprompt_code(
    context: dict,
    broken_code: str,
    error: str,
    tracker: Optional[CostTracker] = None,
) -> str:
    """
    Ask LLM to fix broken code given the error message.
    Returns: fixed pandas code string
    """
    raw = _invoke(
        "fix_code.txt",
        {
            "filename":    context["filename"],
            "schema":      _truncate(context["schema"], _MAX_SCHEMA_CHARS),
            "broken_code": broken_code,
            "error":       error,
        },
        stage="reprompt_code",
        tracker=tracker,
    )
    _, code = _parse_code_response(f"EXPLORE: fix\n{raw}")
    return code


def generate_insights(
    filename: str,
    explore_reason: str,
    result: str,
    user_question: str = "",
    interesting_reason: str = "",
    interesting_result: str = "",
    tracker: Optional[CostTracker] = None,
) -> str:
    """Generate plain-text insight combining both passes."""
    return _invoke(
        "generate_insights.txt",
        {
            "filename":           filename,
            "explore_reason":     explore_reason,
            "result":             _truncate(result, _MAX_RESULT_CHARS),
            "user_question":      user_question or "No specific question provided.",
            "interesting_reason": interesting_reason or "None.",
            "interesting_result": _truncate(interesting_result, _MAX_RESULT_CHARS) if interesting_result else "None.",
        },
        stage="generate_insights",
        tracker=tracker,
    )


# Internal parser
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