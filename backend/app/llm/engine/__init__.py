"""
engine/__init__.py

Public API for the LLM engine package.

Callers (query_service, etc.) should import from here rather than
from the individual sub-modules, so internal restructuring stays invisible.

Usage:
    from app.llm.engine import structured, nlp, INTERESTING_MIN_CHARS
    explore_reason, code = structured.generate_code(context, ...)
    explore_reason, code = nlp.generate_code(context, ...)
"""

from app.llm.engine import structured
from app.llm.engine import nlp
from app.llm.engine.base import INTERESTING_MIN_CHARS

__all__ = [
    "structured",
    "nlp",
    "INTERESTING_MIN_CHARS",
]