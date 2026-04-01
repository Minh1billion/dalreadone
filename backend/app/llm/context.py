from __future__ import annotations

from app.core.config import Config


_DTYPE_SHORT = {"object": "str", "float64": "float", "int64": "int"}

_ID_CARDINALITY_THRESHOLD = 1_000


class EDAContextBuilder:
    """
    Converts a raw EDA JSON report into a compact dict
    suitable for LLM prompting (~3k chars vs ~20k original).
    """

    def build(self, report: dict) -> dict:
        r = report.get("eda_report", report)

        return {
            "overview":      self._overview(r),
            "columns":       self._columns(r),
            "numeric":       self._numeric(r),
            "categorical":   self._categorical(r),
            "distributions": self._distributions(r),
            "correlations":  self._correlations(r),
            "datetime":      self._datetime(r),
            "quality":       self._quality(r),
        }

    def _overview(self, r: dict) -> dict:
        schema  = r.get("schema", {})
        md      = r.get("missing_and_duplicates", {})
        dq      = r.get("data_quality_score", {})
        columns = schema.get("columns", [])

        return {
            "source_file":   r.get("meta", {}).get("source_file"),
            "rows":          schema.get("n_rows"),
            "cols":          schema.get("n_cols"),
            "memory_mb":     schema.get("memory_mb"),
            "duplicate_pct": md.get("duplicate_pct"),
            "quality_score": dq.get("overall_score"),
            "column_names":  [c["name"] for c in columns],
        }

    def _columns(self, r: dict) -> list[dict]:
        """Flatten schema columns to a compact table."""
        missing = (
            r.get("missing_and_duplicates", {}).get("columns", {})
        )
        return [
            {
                "col":      col["name"],
                "type":     _DTYPE_SHORT.get(col["dtype"], col["dtype"]),
                "unique":   col["n_unique"],
                "null_pct": missing.get(col["name"], {}).get("null_pct", 0),
            }
            for col in r.get("schema", {}).get("columns", [])
        ]

    def _numeric(self, r: dict) -> dict:
        """Keep only stats that affect LLM reasoning; drop p25/p75."""
        out = {}
        for col, s in r.get("univariate", {}).get("numeric", {}).items():
            out[col] = {
                "mean":        round(s["mean"], 4),
                "median":      s["median"],
                "std":         round(s["std"], 4),
                "min":         s["min"],
                "max":         s["max"],
                "skewness":    round(s["skewness"], 3),
                "zeros_pct":   s["zeros_pct"],
                "outlier_pct": s["outlier_pct"],
            }
        return out

    def _categorical(self, r: dict) -> dict:
        """
        Skip top_values for ID-like columns (high cardinality + rare_pct=100).
        Keep top_3 for meaningful categorical columns.
        """
        out = {}
        for col, s in r.get("univariate", {}).get("categorical", {}).items():
            is_id_like = (
                s["cardinality"] > _ID_CARDINALITY_THRESHOLD
                and s.get("rare_pct", 0) == 100
            )
            if is_id_like:
                out[col] = {
                    "cardinality": s["cardinality"],
                    "note":        "high-cardinality identifier",
                }
            else:
                out[col] = {
                    "cardinality": s["cardinality"],
                    "mode":        s["mode"],
                    "top_3": [
                        f"{v['value']} ({v['pct']}%)"
                        for v in s.get("top_values", [])[:3]
                    ],
                }
        return out

    def _distributions(self, r: dict) -> dict:
        """Drop histogram_bins + preview_idx. Keep shape + normality + outlier_pct."""
        out = {}
        for col, s in r.get("distributions", {}).items():
            out[col] = {
                "shape":       s.get("dist_type_hint"),
                "is_normal":   s.get("normality_test", {}).get("is_normal"),
                "outlier_pct": s.get("outlier_summary", {}).get("pct"),
            }
        return out

    def _correlations(self, r: dict) -> list[dict]:
        """Only pairs with |value| > 0.1 — filters near-zero noise."""
        return [
            {
                "col_a":  p["col_a"],
                "col_b":  p["col_b"],
                "method": p["method"],
                "value":  p["value"],
            }
            for p in r.get("correlations", {}).get("top_corr_pairs", [])
            if abs(p["value"]) > 0.1
        ]

    def _datetime(self, r: dict) -> dict:
        """Drop null fields and timezone (naive assumed)."""
        out = {}
        for col, s in r.get("datetime", {}).items():
            out[col] = {
                k: v for k, v in s.items()
                if v is not None and k != "timezone"
            }
        return out

    def _quality(self, r: dict) -> dict:
        """Only overall score + flags — drop sub-scores."""
        dq = r.get("data_quality_score", {})
        return {
            "score": dq.get("overall_score"),
            "flags": dq.get("flags", []),
        }