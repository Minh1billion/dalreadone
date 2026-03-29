"""
strategies/structured.py

Context builder for standard structured/tabular datasets
(numeric and low-cardinality categorical columns).

Produces per-column stats appropriate for pandas-based analysis.
Richer stats (std, median, skew, IQR, cardinality) give the LLM
enough signal to choose non-obvious exploration strategies.
"""

import pandas as pd
import numpy as np
from app.llm.strategies.base import ContextStrategy

SAMPLE_ROWS = 5

# Columns with more unique values than this are considered high-cardinality
HIGH_CARDINALITY_THRESHOLD = 20


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
        lines = []
        for col, dtype in zip(df.columns, df.dtypes):
            n_unique = df[col].nunique()
            null_pct = df[col].isna().mean() * 100
            note = ""
            if null_pct > 0:
                note += f", {null_pct:.1f}% null"
            if not pd.api.types.is_numeric_dtype(df[col]):
                note += f", {n_unique} unique values"
            lines.append(f"- {col} ({dtype}){note}")
        return "\n".join(lines)

    def _sample_rows(self, df: pd.DataFrame) -> str:
        return df.head(SAMPLE_ROWS).to_markdown(index=False)

    def _stats(self, df: pd.DataFrame) -> str:
        lines = []
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

        # ── Numeric columns ───────────────────────────────────────────────────
        for col in numeric_cols:
            s         = df[col].dropna()
            null_count = df[col].isna().sum()
            q1, med, q3 = s.quantile([0.25, 0.50, 0.75])
            iqr        = q3 - q1
            skew       = s.skew()
            skew_label = (
                "strongly right-skewed" if skew >  1 else
                "right-skewed"          if skew >  0.5 else
                "strongly left-skewed"  if skew < -1 else
                "left-skewed"           if skew < -0.5 else
                "roughly symmetric"
            )

            # Flag potential bimodal distributions via high std/mean ratio
            cv = s.std() / s.mean() if s.mean() != 0 else 0
            bimodal_hint = " [high variance - possible bimodal]" if cv > 0.8 else ""

            lines.append(
                f"- {col}: "
                f"min={s.min():.2f}, max={s.max():.2f}, "
                f"mean={s.mean():.2f}, median={med:.2f}, "
                f"std={s.std():.2f}, IQR={iqr:.2f}, "
                f"skew={skew_label}, nulls={null_count}"
                f"{bimodal_hint}"
            )

        # ── Categorical columns ───────────────────────────────────────────────
        cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
        for col in cat_cols:
            null_count  = df[col].isna().sum()
            n_unique    = df[col].nunique()
            vc          = df[col].value_counts()
            top_val     = vc.index[0]   if len(vc) > 0 else "N/A"
            top_pct     = vc.iloc[0] / len(df) * 100 if len(vc) > 0 else 0
            top2_val    = vc.index[1]   if len(vc) > 1 else None
            top2_pct    = vc.iloc[1] / len(df) * 100 if len(vc) > 1 else 0

            # Concentration signal: is top category disproportionately large?
            concentration = ""
            if len(vc) > 1 and top_pct > top2_pct * 2:
                concentration = f" [concentrated: top value is {top_pct/top2_pct:.1f}× second]"

            if n_unique <= HIGH_CARDINALITY_THRESHOLD:
                # Show full distribution for low-cardinality categoricals
                dist = ", ".join(f"{v}={vc[v]/len(df)*100:.1f}%" for v in vc.index[:8])
                lines.append(
                    f"- {col}: {n_unique} categories [{dist}], nulls={null_count}"
                    f"{concentration}"
                )
            else:
                lines.append(
                    f"- {col}: {n_unique} unique values (high-cardinality), "
                    f"top={top_val!r} ({top_pct:.1f}%), "
                    f"2nd={top2_val!r} ({top2_pct:.1f}%), "
                    f"nulls={null_count}"
                    f"{concentration}"
                )

        # ── Cross-column signals ──────────────────────────────────────────────
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr()
            strong_pairs = []
            seen = set()
            for c1 in numeric_cols:
                for c2 in numeric_cols:
                    if c1 == c2 or (c2, c1) in seen:
                        continue
                    seen.add((c1, c2))
                    r = corr.loc[c1, c2]
                    if abs(r) >= 0.3:
                        direction = "positive" if r > 0 else "negative"
                        strength  = "strong" if abs(r) >= 0.6 else "moderate"
                        strong_pairs.append(f"{c1}↔{c2}: {direction} {strength} (r={r:.2f})")
            if strong_pairs:
                lines.append(f"\nNotable correlations: {'; '.join(strong_pairs)}")

        return "\n".join(lines)