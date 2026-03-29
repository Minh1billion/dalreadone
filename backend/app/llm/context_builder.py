import io
import pandas as pd

from app.llm.text_detector import is_text_heavy
from app.llm.strategies import StructuredStrategy, NLPStrategy


def build_dataframe_context(
    file_bytes: bytes,
    filename: str,
    stopwords_config: dict | None = None,   # ← thêm
) -> dict:
    df = _load_df(file_bytes, filename)
    heavy, text_cols = is_text_heavy(df)
    strategy = (
        NLPStrategy(text_cols, stopwords_config=stopwords_config)
        if heavy
        else StructuredStrategy()
    )
    return strategy.build(df, filename)


def _load_df(file_bytes: bytes, filename: str) -> pd.DataFrame:
    buf = io.BytesIO(file_bytes)
    if filename.endswith(".csv"):
        return pd.read_csv(buf)
    return pd.read_excel(buf)