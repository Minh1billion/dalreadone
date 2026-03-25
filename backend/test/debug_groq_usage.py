"""
debug_groq_usage.py

Run this once to inspect the exact structure of usage_metadata
that Groq returns, so we can fix the token extraction in llm_engine.py.

Usage:
    python -m app.test.debug_groq_usage
"""

import json
from langchain_groq import ChatGroq
from app.core.config import Config

llm = ChatGroq(
    model=Config.MODEL_ID,
    api_key=Config.GROQ_API_KEY,
    temperature=0.2,
    max_tokens=50,
)

response = llm.invoke("Say hello in one word.")

print("=== response type ===")
print(type(response))

print("\n=== response.__dict__ ===")
print(json.dumps(
    {k: str(v) for k, v in response.__dict__.items()},
    indent=2
))

print("\n=== usage_metadata ===")
meta = getattr(response, "usage_metadata", None)
print(repr(meta))

print("\n=== response_metadata ===")
rmeta = getattr(response, "response_metadata", None)
print(repr(rmeta))