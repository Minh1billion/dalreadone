"""
strategies/structured.py

Context builder for standard structured/tabular datasets
(numeric and low-cardinality categorical columns).

Produces per-column stats appropriate for pandas-based analysis:
numeric columns → min, max, mean, null count
categorical columns → top value, null count
"""

import pandas as pd
from app.llm.strategies.base import ContextStrategy

# Number of sample rows included in the prompt
SAMPLE_ROWS = 5


class StructuredStrategy(ContextStrategy):

    def build(self, df: pd.DataFrame, filename: str) -> dict:
        return {
            "filename":    filename,
            "schema":      self._schema(df),
            "sample_rows": self._sample_rows(df),
            "stats":       self._stats(df),
            "df":          df,
            "is_nlp":      False,
        }

    def _schema(self, df: pd.DataFrame) -> str:
        return "\n".join(
            f"- {col} ({dtype})"
            for col, dtype in zip(df.columns, df.dtypes)
        )

    def _sample_rows(self, df: pd.DataFrame) -> str:
        return df.head(SAMPLE_ROWS).to_markdown(index=False)

    def _stats(self, df: pd.DataFrame) -> str:
        lines = []
        for col in df.columns:
            null_count = df[col].isna().sum()
            if pd.api.types.is_numeric_dtype(df[col]):
                lines.append(
                    f"- {col}: min={df[col].min()}, max={df[col].max()}, "
                    f"mean={df[col].mean():.2f}, nulls={null_count}"
                )
            else:
                top = (
                    df[col].value_counts().index[0]
                    if df[col].notna().any() else "N/A"
                )
                lines.append(f"- {col}: top_value={top}, nulls={null_count}")
        return "\n".join(lines)