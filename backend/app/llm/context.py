from __future__ import annotations

from app.core.config import Config


# Raw dtype → short label for LLM readability
_DTYPE_SHORT: dict[str, str] = {
    "object":          "str",
    "string":          "str",
    "float64":         "float",
    "float32":         "float",
    "int64":           "int",
    "int32":           "int",
    "int16":           "int",
    "int8":            "int",
    "uint64":          "int",
    "uint32":          "int",
    "bool":            "bool",
    "category":        "category",
    "datetime64[ns]":  "datetime",
    "datetime64[us]":  "datetime",
    "timedelta64[ns]": "timedelta",
}

# int/float columns with ≤ this many unique values are likely categorical labels
_LOW_CARD_NUMERIC_THRESHOLD = 20

# str/object columns with > this many unique values are likely IDs
_ID_CARDINALITY_THRESHOLD = 1_000


class EDAContextBuilder:
    def build(self, report: dict) -> dict:
        r = report.get("eda_report", report)

        columns = self._columns(r)

        # Pre-compute column classification lists for prompt-level awareness
        likely_cat_cols = [c["col"] for c in columns if c.get("likely_cat")]
        datetime_cols   = [c["col"] for c in columns if c["type"] == "datetime"]
        bool_cols       = [c["col"] for c in columns if c["type"] == "bool"]
        id_cols         = [
            c["col"] for c in columns
            if c["type"] == "str" and c["unique"] > _ID_CARDINALITY_THRESHOLD
        ]

        return {
            "overview":        self._overview(r, likely_cat_cols, datetime_cols),
            "columns":         columns,
            "col_roles": {
                "likely_categorical_numeric": likely_cat_cols,
                "datetime":                  datetime_cols,
                "boolean":                   bool_cols,
                "id_like":                   id_cols,
            },
            "numeric":         self._numeric(r, likely_cat_cols),
            "categorical":     self._categorical(r, likely_cat_cols, r),
            "distributions":   self._distributions(r),
            "correlations":    self._correlations(r),
            "datetime":        self._datetime(r),
            "quality":         self._quality(r),
        }

    def _overview(self, r: dict, likely_cat_cols: list[str], datetime_cols: list[str]) -> dict:
        schema  = r.get("schema", {})
        md      = r.get("missing_and_duplicates", {})
        dq      = r.get("data_quality_score", {})
        columns = schema.get("columns", [])

        return {
            "source_file":          r.get("meta", {}).get("source_file"),
            "rows":                 schema.get("n_rows"),
            "cols":                 schema.get("n_cols"),
            "memory_mb":            schema.get("memory_mb"),
            "duplicate_pct":        md.get("duplicate_pct"),
            "quality_score":        dq.get("overall_score"),
            "column_names":         [c["name"] for c in columns],
            "likely_categorical_numeric_cols": likely_cat_cols,
            "datetime_cols":                   datetime_cols,
        }

    def _columns(self, r: dict) -> list[dict]:
        """
        Flatten schema columns to an enriched compact table.

        Each entry includes:
        - dtype: raw pandas dtype string (e.g. "int64", "object")
        - type:  short alias (e.g. "int", "str", "datetime")
        - unique: number of unique values
        - null_pct: % of nulls
        - likely_cat: True if numeric but cardinality ≤ threshold →
            the LLM must treat this column as a label, not a measurement
        """
        missing = r.get("missing_and_duplicates", {}).get("columns", {})
        out = []
        for col in r.get("schema", {}).get("columns", []):
            raw_dtype  = col.get("dtype", "object")
            short_type = _DTYPE_SHORT.get(raw_dtype, raw_dtype)
            n_unique   = col.get("n_unique", 0)

            is_numeric  = short_type in ("int", "float")
            likely_cat  = is_numeric and n_unique <= _LOW_CARD_NUMERIC_THRESHOLD

            out.append({
                "col":        col["name"],
                "dtype":      raw_dtype,           # raw - exact pandas dtype
                "type":       short_type,           # short alias
                "unique":     n_unique,
                "null_pct":   missing.get(col["name"], {}).get("null_pct", 0),
                "likely_cat": likely_cat,
                **({"note": "numeric dtype but low cardinality - treat as categorical label, not a continuous measurement"} if likely_cat else {}),
            })
        return out

    def _numeric(self, r: dict, likely_cat_cols: list[str]) -> dict:
        """
        Keep stats that affect LLM reasoning.
        Exclude likely_cat columns - they are not continuous measurements
        and their 'outliers' / 'skewness' stats are meaningless as such.
        """
        out = {}
        for col, s in r.get("univariate", {}).get("numeric", {}).items():
            if col in likely_cat_cols:
                out[col] = {
                    "_skip_reason": "likely_cat - see col_roles.likely_categorical_numeric",
                    "unique":       s.get("n_unique") or len(set()),
                    "min":          s.get("min"),
                    "max":          s.get("max"),
                }
                continue

            v_min  = s.get("min", 0)
            v_max  = s.get("max", 0)
            out[col] = {
                "mean":         round(s["mean"], 4),
                "median":       s["median"],
                "std":          round(s["std"], 4),
                "min":          v_min,
                "max":          v_max,
                "value_range":  round(v_max - v_min, 4),
                "skewness":     round(s["skewness"], 3),
                "zeros_pct":    s["zeros_pct"],
                "outlier_pct":  s["outlier_pct"],

                "has_negatives": v_min < 0,
            }
        return out

    def _categorical(self, r: dict, likely_cat_cols: list[str], full_r: dict) -> dict:
        """
        Categorical columns from EDA + numeric-as-category columns merged in.

        For likely_cat columns we pull min/max/unique from the numeric stats
        so the LLM gets the full picture in one place.
        """
        out: dict = {}

        for col, s in r.get("univariate", {}).get("categorical", {}).items():
            is_id_like = (
                s["cardinality"] > _ID_CARDINALITY_THRESHOLD
                and s.get("rare_pct", 0) == 100
            )
            if is_id_like:
                out[col] = {
                    "cardinality": s["cardinality"],
                    "note":        "high-cardinality identifier - skip encoding",
                }
            else:
                out[col] = {
                    "cardinality": s["cardinality"],
                    "mode":        s["mode"],
                    "top_3": [
                        f"{v['value']} ({v['pct']}%)"
                        for v in s.get("top_values", [])[:3]
                    ],
                    "rare_pct": s.get("rare_pct", 0),
                }

        numeric_stats = full_r.get("univariate", {}).get("numeric", {})
        for col in likely_cat_cols:
            if col in out:
                continue
            s = numeric_stats.get(col, {})
            out[col] = {
                "dtype":         "numeric (int/float) - but is a categorical label",
                "cardinality":   s.get("n_unique", "?"),
                "min":           s.get("min"),
                "max":           s.get("max"),
                "zeros_pct":     s.get("zeros_pct"),
                "note": (
                    "This column has numeric dtype but very low cardinality. "
                    "It must be treated as a categorical/label column. "
                    "Use LabelStrategy or OrdinalStrategy, NOT scaling or outlier handling."
                ),
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
        """Only pairs with |value| > 0.1 - filters near-zero noise."""
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
        """Only overall score + flags - drop sub-scores."""
        dq = r.get("data_quality_score", {})
        return {
            "score": dq.get("overall_score"),
            "flags": dq.get("flags", []),
        }