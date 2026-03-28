"""
strategies/base.py

Abstract base class for all context-building strategies.

Each strategy is responsible for:
    - building the schema string
    - building the sample_rows markdown
    - building the stats string
    - returning a context dict consumed by the LLM engine

Required keys in every context dict:
    filename    : str
    schema      : str
    sample_rows : str
    stats       : str
    df          : pd.DataFrame
    is_nlp      : bool   — tells query_service which engine module to use
"""

from abc import ABC, abstractmethod
import pandas as pd


class ContextStrategy(ABC):

    @abstractmethod
    def build(self, df: pd.DataFrame, filename: str) -> dict:
        """Build and return a context dict ready for the LLM prompt."""
        ...