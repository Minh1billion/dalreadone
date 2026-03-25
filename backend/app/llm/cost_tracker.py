"""
cost_tracker.py

Tracks token usage and estimated cost for every LLM call in the pipeline.

Groq llama-3.3-70b-versatile pricing (as of 2025):
  Input  : $0.59 / 1M tokens
  Output : $0.79 / 1M tokens

Usage:
    from app.llm.cost_tracker import CostTracker

    tracker = CostTracker()
    tracker.record("generate_code", prompt_tokens=800, completion_tokens=300)
    tracker.record("generate_insights", prompt_tokens=1200, completion_tokens=400)
    print(tracker.summary())
    report = tracker.report()   # attach to API response for frontend display
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


# Pricing - update here if Groq changes rates
_PRICE_INPUT_PER_M  = 0.59   # USD per 1 million input tokens
_PRICE_OUTPUT_PER_M = 0.79   # USD per 1 million output tokens


def _cost_usd(prompt_tokens: int, completion_tokens: int) -> float:
    return (
        prompt_tokens    * _PRICE_INPUT_PER_M  / 1_000_000
        + completion_tokens * _PRICE_OUTPUT_PER_M / 1_000_000
    )



# Data classes


@dataclass
class CallRecord:
    stage: str               # e.g. "generate_code", "reprompt_code#1"
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    latency_ms: int          # wall-clock ms for the LLM call
    skipped: bool = False    # True when the call was skipped by an optimisation
    skip_reason: str = ""


@dataclass
class CostTracker:
    """
    Accumulates per-call records for one query pipeline run.

    Attach one instance to each run_query() call and return
    the .report() dict inside the API response so the frontend
    can display real cost data.
    """
    records: list[CallRecord] = field(default_factory=list)
    _query_start: float = field(default_factory=time.monotonic, repr=False)

    
    # Recording
    def record(
        self,
        stage: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int = 0,
    ) -> CallRecord:
        """Add a completed LLM call."""
        rec = CallRecord(
            stage=stage,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=_cost_usd(prompt_tokens, completion_tokens),
            latency_ms=latency_ms,
        )
        self.records.append(rec)
        return rec

    def record_skip(self, stage: str, reason: str) -> CallRecord:
        """Record a stage that was skipped by an optimisation (zero cost)."""
        rec = CallRecord(
            stage=stage,
            prompt_tokens=0,
            completion_tokens=0,
            cost_usd=0.0,
            latency_ms=0,
            skipped=True,
            skip_reason=reason,
        )
        self.records.append(rec)
        return rec

    
    # Aggregation
    @property
    def total_prompt_tokens(self) -> int:
        return sum(r.prompt_tokens for r in self.records)

    @property
    def total_completion_tokens(self) -> int:
        return sum(r.completion_tokens for r in self.records)

    @property
    def total_tokens(self) -> int:
        return self.total_prompt_tokens + self.total_completion_tokens

    @property
    def total_cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.records)

    @property
    def total_latency_ms(self) -> int:
        return int((time.monotonic() - self._query_start) * 1000)

    @property
    def skipped_stages(self) -> list[str]:
        return [r.stage for r in self.records if r.skipped]

    
    # Output
    def summary(self) -> str:
        """Human-readable one-liner for server logs."""
        lines = [
            f"[cost_tracker] query total: "
            f"{self.total_tokens} tokens | "
            f"${self.total_cost_usd:.6f} | "
            f"{self.total_latency_ms}ms"
        ]
        for r in self.records:
            if r.skipped:
                lines.append(f"  {r.stage:30s}  SKIPPED  ({r.skip_reason})")
            else:
                lines.append(
                    f"  {r.stage:30s}  "
                    f"in={r.prompt_tokens:5d}  out={r.completion_tokens:4d}  "
                    f"${r.cost_usd:.6f}  {r.latency_ms}ms"
                )
        return "\n".join(lines)

    def report(self) -> dict:
        """
        Structured dict included in the API response under 'cost_report'.
        Frontend can display this in a dev panel or log it.
        """
        return {
            "total_tokens": self.total_tokens,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_latency_ms": self.total_latency_ms,
            "skipped_stages": self.skipped_stages,
            "calls": [
                {
                    "stage": r.stage,
                    "prompt_tokens": r.prompt_tokens,
                    "completion_tokens": r.completion_tokens,
                    "cost_usd": round(r.cost_usd, 6),
                    "latency_ms": r.latency_ms,
                    "skipped": r.skipped,
                    "skip_reason": r.skip_reason,
                }
                for r in self.records
            ],
        }