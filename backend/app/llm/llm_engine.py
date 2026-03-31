from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.config import Config

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int
    completion_tokens: int
    model: str


class BaseLLMEngine(ABC):
    @abstractmethod
    async def ainvoke(
        self,
        system_prompt: str,
        user_message: str,
    ) -> LLMResponse: ...


class GroqEngine(BaseLLMEngine):
    def __init__(self) -> None:
        from langchain_groq import ChatGroq
        self._llm = ChatGroq(
            api_key=Config.GROQ_API_KEY,
            model=Config.MODEL_ID,
            temperature=Config.DA_TEMPERATURE,
            max_tokens=Config.DA_MAX_TOKENS,
        )

    async def ainvoke(self, system_prompt: str, user_message: str) -> LLMResponse:
        from langchain_core.messages import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
        resp = await self._llm.ainvoke(messages)

        usage = resp.response_metadata.get("token_usage", {})
        return LLMResponse(
            content=resp.content,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            model=usage.get("model_name", Config.MODEL_ID) or Config.MODEL_ID,
        )


_REGISTRY: dict[str, type[BaseLLMEngine]] = {
    "groq": GroqEngine,
}


def make_engine(provider: str | None = None) -> BaseLLMEngine:
    import os
    key = (provider or os.environ.get("LLM_PROVIDER", "groq")).lower()
    cls = _REGISTRY.get(key)
    if cls is None:
        raise ValueError(f"Unknown LLM provider '{key}'. Available: {list(_REGISTRY)}")
    return cls()