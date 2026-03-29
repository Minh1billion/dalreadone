import re
import time
from pathlib import Path
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

from app.core.config import Config
from app.llm.cost_tracker import CostTracker

TEMPLATE_DIR = Path(__file__).parent.parent / "template"

STAGE_MAX_TOKENS: dict[str, int] = {
    "generate_code":          900,
    "generate_code_nlp":      900,
    "find_interesting":       900,
    "find_interesting_nlp":   900,
    "reprompt_code":          700,
    "generate_insights":      500,
}

MAX_SCHEMA_CHARS      = 3_000
MAX_SAMPLE_ROWS_CHARS = 2_000
MAX_STATS_CHARS       = 2_000
MAX_RESULT_CHARS      = 4_000
INTERESTING_MIN_CHARS = 200

_RATE_LIMIT_MAX_RETRIES = 4
_RATE_LIMIT_BASE_DELAY  = 1.0
_MAX_WAIT_SECONDS       = 30.0
_RETRY_AFTER_RE = re.compile(r"try again in (\d+)m([\d.]+)s", re.IGNORECASE)


def _make_llm(stage: str, api_key: str = None) -> ChatGroq:
    base_stage = stage.split("#")[0]
    return ChatGroq(
        model=Config.MODEL_ID,
        api_key=api_key or Config.GROQ_API_KEY,
        temperature=0.2,
        max_tokens=STAGE_MAX_TOKENS.get(base_stage, 900),
    )

def _load_template(filename: str) -> PromptTemplate:
    text = (TEMPLATE_DIR / filename).read_text()
    return PromptTemplate.from_template(text)

def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n... [truncated to {max_chars} chars]"

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

def _parse_retry_after(message: str) -> float | None:
    m = _RETRY_AFTER_RE.search(message)
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    return None


def invoke_with_retry(
    chain,
    variables: dict,
    stage: str,
    tracker: Optional[CostTracker] = None,
) -> str:
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
    api_key: str = None,
) -> str:
    prompt = _load_template(template_file)
    llm    = _make_llm(stage, api_key=api_key)
    chain  = prompt | llm
    return invoke_with_retry(chain, variables, stage=stage, tracker=tracker)


def parse_code_response(raw: str) -> tuple[str, str]:
    """
    Extract the EXPLORE reason and python code block from a raw LLM response.

    Parsing is intentionally lenient:
    - Accepts ``` python (with space) as well as ```python
    - Falls back to treating the entire response as code if no fenced block
      is found, so a truncated or improperly formatted response still produces
      a repromptable error instead of crashing the whole pipeline.
    - Never raises — returns ("", "") if truly nothing useful was found,
      which run_with_retry treats as an empty-result error and reprompts.
    """
    explore_reason = ""
    code_lines: list[str] = []
    in_code_block = False
    found_fence   = False

    for line in raw.splitlines():
        stripped = line.strip()

        if stripped.startswith("EXPLORE:"):
            explore_reason = stripped.replace("EXPLORE:", "").strip()
            continue

        # Accept ```python or ``` python
        if re.match(r"^```\s*python\s*$", stripped, re.IGNORECASE):
            in_code_block = True
            found_fence   = True
            continue

        if stripped == "```" and in_code_block:
            in_code_block = False
            continue

        if in_code_block:
            code_lines.append(line)

    code = "\n".join(code_lines).strip()

    # Fallback: if no fenced block was found but the response looks like code,
    # use the whole response so the sandbox can attempt execution and produce
    # a meaningful error message for the reprompt rather than failing silently.
    if not found_fence and not code:
        candidate = raw.strip()
        if "result" in candidate and "=" in candidate:
            return explore_reason, candidate

    return explore_reason, code