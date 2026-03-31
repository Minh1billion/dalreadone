from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

_DEFAULT_PRICES: dict[str, dict[str, float]] = {
    "llama-3.3-70b-versatile":      {"prompt": 0.59,  "completion": 0.79},
    "llama-3.1-8b-instant":         {"prompt": 0.05,  "completion": 0.08},
    "mixtral-8x7b-32768":           {"prompt": 0.24,  "completion": 0.24},
    "gemma2-9b-it":                 {"prompt": 0.20,  "completion": 0.20},
    "__default__":                  {"prompt": 0.59,  "completion": 0.79},
}


@dataclass
class ChainUsage:
    chain_name: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    model: str = ""

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class CostTracker:
    def __init__(self, price_table: dict | None = None) -> None:
        self._prices = price_table or _DEFAULT_PRICES
        self._chains: dict[str, ChainUsage] = {}

    def record(
        self,
        chain_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
    ) -> None:
        prices = self._prices.get(model.lower(), self._prices["__default__"])
        cost = (
            prompt_tokens     / 1_000_000 * prices["prompt"]
            + completion_tokens / 1_000_000 * prices["completion"]
        )
        self._chains[chain_name] = ChainUsage(
            chain_name=chain_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=round(cost, 8),
            model=model,
        )

    @property
    def total_prompt_tokens(self) -> int:
        return sum(c.prompt_tokens for c in self._chains.values())

    @property
    def total_completion_tokens(self) -> int:
        return sum(c.completion_tokens for c in self._chains.values())

    @property
    def total_tokens(self) -> int:
        return self.total_prompt_tokens + self.total_completion_tokens

    @property
    def total_cost_usd(self) -> float:
        return round(sum(c.cost_usd for c in self._chains.values()), 8)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": {
                "total_prompt_tokens":     self.total_prompt_tokens,
                "total_completion_tokens": self.total_completion_tokens,
                "total_tokens":            self.total_tokens,
                "total_cost_usd":          self.total_cost_usd,
            },
            "per_chain": [
                {
                    "chain":              c.chain_name,
                    "model":              c.model,
                    "prompt_tokens":      c.prompt_tokens,
                    "completion_tokens":  c.completion_tokens,
                    "total_tokens":       c.total_tokens,
                    "cost_usd":           c.cost_usd,
                }
                for c in self._chains.values()
            ],
        }