"""
llm_engine.py

LLM call layer with three cost optimisations applied without touching output quality:

  1. max_tokens per call
  2. Prompt truncation
  3. Pass-2 skip heuristic
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

_MAX_TOKENS: dict[str, int] = {
    "generate_code":       900,
    "find_interesting":    900,
    "reprompt_code":       700,
    "generate_insights":   500,
}

_MAX_SCHEMA_CHARS      = 3_000
_MAX_SAMPLE_ROWS_CHARS = 2_000
_MAX_STATS_CHARS       = 2_000
_MAX_RESULT_CHARS      = 4_000

INTERESTING_MIN_CHARS = 200

_RATE_LIMIT_MAX_RETRIES = 4
_RATE_LIMIT_BASE_DELAY  = 1.0
_MAX_WAIT_SECONDS       = 30.0
_RETRY_AFTER_RE = re.compile(r"try again in (\d+)m([\d.]+)s", re.IGNORECASE)


def _extract_token_counts(response) -> tuple[int, int]:
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

    out_chars = len(getattr(response, "content", "") or "")
    return 0, max(1, out_chars // 4)


def _make_llm(stage: str) -> ChatGroq:
    # Normalise numbered stages like "reprompt_code#1" -> "reprompt_code"
    base_stage = stage.split("#")[0]
    return ChatGroq(
        model=Config.MODEL_ID,
        api_key=Config.GROQ_API_KEY,
        temperature=0.2,
        max_tokens=_MAX_TOKENS.get(base_stage, 900),
    )


def _truncate(text: str, max_chars: int) -> str:
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
    raw = _invoke(
        "generate_code.txt",
        {
            "filename":      context["filename"],
            "schema":        _truncate(context["schema"],      _MAX_SCHEMA_CHARS),
            "sample_rows":   _truncate(context["sample_rows"], _MAX_SAMPLE_ROWS_CHARS),
            "stats":         _truncate(context["stats"],       _MAX_STATS_CHARS),
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
    if len(result_str) < INTERESTING_MIN_CHARS:
        return "", ""

    raw = _invoke(
        "find_interesting.txt",
        {
            "filename":       context["filename"],
            "schema":         _truncate(context["schema"],     _MAX_SCHEMA_CHARS),
            "explore_reason": explore_reason,
            "result":         _truncate(result_str,            _MAX_RESULT_CHARS),
            "user_question":  user_question or "No specific question provided.",
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
    stage: str = "reprompt_code",
) -> str:
    raw = _invoke(
        "fix_code.txt",
        {
            "filename":    context["filename"],
            "schema":      _truncate(context["schema"], _MAX_SCHEMA_CHARS),
            "broken_code": broken_code,
            "error":       error,
        },
        stage=stage,
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


def _parse_code_response(raw: str) -> tuple[str, str]:
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