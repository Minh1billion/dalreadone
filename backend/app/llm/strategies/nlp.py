import re
import collections
import pandas as pd

from app.llm.strategies.base import ContextStrategy
from app.llm.strategies.features import compute_nlp_features

SAMPLE_ROWS    = 5
MAX_CELL_CHARS = 200
TOP_WORDS      = 20
TOP_BIGRAMS    = 10
MIN_WORD_LEN   = 2

DEFAULT_STOPWORDS = {
    "this", "that", "with", "from", "have", "been", "were", "they",
    "their", "there", "what", "when", "will", "would", "could", "should",
    "which", "about", "into", "than", "then", "some", "your", "just",
    "also", "very", "more", "most", "such", "after", "before", "other",
}


def resolve_stopwords(config: dict | None) -> frozenset[str]:
    if not config:
        return frozenset(DEFAULT_STOPWORDS)
    words = set(DEFAULT_STOPWORDS)
    words |= {w.lower().strip() for w in config.get("add",    [])}
    words -= {w.lower().strip() for w in config.get("remove", [])}
    return frozenset(words)


class NLPStrategy(ContextStrategy):

    def __init__(self, text_cols: list[str], stopwords_config: dict | None = None) -> None:
        self._text_cols = text_cols
        self._stopwords = resolve_stopwords(stopwords_config)

    def build(self, df: pd.DataFrame, filename: str) -> dict:
        return {
            "filename":     filename,
            "schema":       self._schema(df),
            "sample_rows":  self._sample_rows(df),
            "stats":        self._stats(df),
            "nlp_features": compute_nlp_features(df, self._text_cols, self._stopwords),
            "df":           df,
            "text_cols":    self._text_cols,
            "is_nlp":       True,
            "stopwords":    sorted(self._stopwords),
        }

    def _schema(self, df: pd.DataFrame) -> str:
        return "\n".join(
            f"- {col} ({dtype})"
            for col, dtype in zip(df.columns, df.dtypes)
        )

    def _sample_rows(self, df: pd.DataFrame) -> str:
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

    def _tokenize(self, text: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z]+", text.lower())
        return [t for t in tokens if len(t) >= MIN_WORD_LEN and t not in self._stopwords]

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