"""
context_builder.py

Single entry point for building an LLM context dict from raw file bytes.

Responsibilities:
    1. Load the file into a DataFrame (CSV or Excel)
    2. Detect whether the data is text-heavy (text_detector)
    3. Delegate to the appropriate strategy (StructuredStrategy / NLPStrategy)

Nothing else. All schema/stats/feature logic lives in the strategy classes.
"""

import io
import pandas as pd

from app.llm.text_detector import is_text_heavy
from app.llm.strategies import StructuredStrategy, NLPStrategy


def build_dataframe_context(file_bytes: bytes, filename: str) -> dict:
    """
    Load a CSV or Excel file and return a context dict for the LLM prompt.

    The returned dict always contains at minimum:
        filename, schema, sample_rows, stats, df, is_nlp

    NLP contexts additionally contain:
        nlp_features, text_cols

    Args:
        file_bytes : Raw file content.
        filename   : Original filename — used to infer format and shown to LLM.

    Returns:
        Context dict consumed by engine/structured.py or engine/nlp.py.
    """
    df = _load_df(file_bytes, filename)
    heavy, text_cols = is_text_heavy(df)
    non_text_cols = [col for col in df.columns if col not in text_cols]
    strategy = NLPStrategy(text_cols) if heavy else StructuredStrategy()
    return strategy.build(df, filename)


def _load_df(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Parse raw bytes into a DataFrame based on file extension."""
    buf = io.BytesIO(file_bytes)
    if filename.endswith(".csv"):
        return pd.read_csv(buf)
    return pd.read_excel(buf)