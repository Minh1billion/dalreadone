"""
strategies/nlp.py

Context builder for text-heavy datasets
(reviews, comments, articles, transcripts, survey responses, etc.).

Replaces generic tabular stats with NLP-specific metrics:
    - vocabulary size, avg char/word count per text column
    - top words and bigrams
    - pre-computed features: sentiment, TF-IDF keywords, topic clusters,
      length distribution (via strategies/features.py)

The resulting context dict contains an extra "nlp_features" key that
the NLP engine (engine/nlp.py) injects into its prompts.
"""

import re
import collections
import pandas as pd

from app.llm.strategies.base import ContextStrategy
from app.llm.strategies.features import compute_nlp_features

# Number of sample rows to show in the prompt
SAMPLE_ROWS = 5
# Max characters per cell in sample to avoid bloating the prompt
MAX_CELL_CHARS = 200
# Top N words/bigrams shown in stats (separate from TF-IDF keywords)
TOP_WORDS   = 20
TOP_BIGRAMS = 10
# Minimum token length for stats word counting
MIN_WORD_LEN = 4

_STOPWORDS = {
    "this", "that", "with", "from", "have", "been", "were", "they",
    "their", "there", "what", "when", "will", "would", "could", "should",
    "which", "about", "into", "than", "then", "some", "your", "just",
    "also", "very", "more", "most", "such", "after", "before", "other",
}


class NLPStrategy(ContextStrategy):

    def __init__(self, text_cols: list[str]) -> None:
        self._text_cols = text_cols

    def build(self, df: pd.DataFrame, filename: str) -> dict:
        return {
            "filename":     filename,
            "schema":       self._schema(df),
            "sample_rows":  self._sample_rows(df),
            "stats":        self._stats(df),
            "nlp_features": compute_nlp_features(df, self._text_cols),
            "df":           df,
            "text_cols":    self._text_cols,
            "is_nlp":       True,
        }
    

    def _schema(self, df: pd.DataFrame) -> str:
        return "\n".join(
            f"- {col} ({dtype})"
            for col, dtype in zip(df.columns, df.dtypes)
        )

    def _sample_rows(self, df: pd.DataFrame) -> str:
        """Sample rows with long cells truncated to keep prompts compact."""
        sample = df[self._text_cols].head(SAMPLE_ROWS).copy()
        for col in self._text_cols:
            sample[col] = sample[col].astype(str).str[:MAX_CELL_CHARS]
        return sample.to_markdown(index=False)

    def _stats(self, df: pd.DataFrame) -> str:
        return "\n\n".join(
            self._col_stats(df[col], col) for col in self._text_cols
        )

    def _col_stats(self, series: pd.Series, col: str) -> str:
        non_null   = series.dropna()
        null_count = series.isna().sum()
        avg_chars  = non_null.astype(str).str.len().mean()
        avg_words  = self._avg_word_count(series)
        vocab      = self._vocab_size(series)
        words      = self._top_words(series)
        bigrams    = self._top_bigrams(series)

        word_str   = ", ".join(f"{w}({c})" for w, c in words)
        bigram_str = ", ".join(f'"{b}"({c})' for b, c in bigrams)

        return (
            f"Column: {col}\n"
            f"  rows={len(series)}, nulls={null_count}, "
            f"avg_chars={avg_chars:.0f}, avg_words={avg_words:.1f}, "
            f"vocab_size={vocab}\n"
            f"  top_words   : {word_str}\n"
            f"  top_bigrams : {bigram_str}"
        )

    
    # Text utilities
    def _tokenize(self, text: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z]+", text.lower())
        return [t for t in tokens if len(t) >= MIN_WORD_LEN and t not in _STOPWORDS]

    def _avg_word_count(self, series: pd.Series) -> float:
        return series.dropna().astype(str).apply(lambda x: len(x.split())).mean()

    def _vocab_size(self, series: pd.Series) -> int:
        words: set[str] = set()
        for val in series.dropna().astype(str):
            words.update(self._tokenize(val))
        return len(words)

    def _top_words(self, series: pd.Series) -> list[tuple[str, int]]:
        counter: collections.Counter = collections.Counter()
        for val in series.dropna().astype(str):
            counter.update(self._tokenize(val))
        return counter.most_common(TOP_WORDS)

    def _top_bigrams(self, series: pd.Series) -> list[tuple[str, int]]:
        counter: collections.Counter = collections.Counter()
        for val in series.dropna().astype(str):
            tokens = self._tokenize(val)
            counter.update(f"{a} {b}" for a, b in zip(tokens, tokens[1:]))
        return counter.most_common(TOP_BIGRAMS)