from __future__ import annotations

from app.core.config import Config


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
    "category":        "cat",
    "datetime64[ns]":  "dt",
    "datetime64[us]":  "dt",
    "timedelta64[ns]": "td",
}

_LOW_CARD_NUMERIC_THRESHOLD = 20
_ID_CARDINALITY_THRESHOLD   = 1_000
_CORR_MIN_ABS               = 0.3
_CORR_MAX_PAIRS             = 8
_CAT_TOP_N                  = 2


class EDAContextBuilder:
    def build(self, report: dict) -> dict:
        r = report.get("eda_report", report)

        columns         = self._columns(r)
        likely_cat_cols = [c["col"] for c in columns if c.get("lc")]
        datetime_cols   = [c["col"] for c in columns if c["t"] == "dt"]
        bool_cols       = [c["col"] for c in columns if c["t"] == "bool"]
        id_cols         = [
            c["col"] for c in columns
            if c["t"] == "str" and c["u"] > _ID_CARDINALITY_THRESHOLD
        ]

        return {
            "overview":     self._overview(r, likely_cat_cols, datetime_cols),
            "col_roles": {
                "lc_numeric": likely_cat_cols,   # treat as label, not measurement
                "datetime":   datetime_cols,
                "boolean":    bool_cols,
                "id_like":    id_cols,
            },
            "columns":      columns,
            "numeric":      self._numeric(r, likely_cat_cols),
            "categorical":  self._categorical(r, likely_cat_cols, r),
            "correlations": self._correlations(r),
            "datetime":     self._datetime(r),
            "quality":      self._quality(r),
            # distributions omitted - shape/normality captured in numeric.skew
            # and numeric.outlier_pct; histogram bins are never useful for LLM
        }


    def _overview(self, r: dict, likely_cat_cols: list[str], datetime_cols: list[str]) -> dict:
        schema = r.get("schema", {})
        md     = r.get("missing_and_duplicates", {})
        dq     = r.get("data_quality_score", {})
        return {
            "file":      r.get("meta", {}).get("source_file"),
            "rows":      schema.get("n_rows"),
            "cols":      schema.get("n_cols"),
            "dup_pct":   md.get("duplicate_pct"),
            "q_score":   dq.get("overall_score"),
            "col_names": [c["name"] for c in schema.get("columns", [])],
            "lc_cols":   likely_cat_cols,   # quick ref - full detail in col_roles
            "dt_cols":   datetime_cols,
        }


    def _columns(self, r: dict) -> list[dict]:
        """
        Compact column table.  Short keys to save tokens:
          col → col name
          t   → short type (str/int/float/bool/dt/cat)
          u   → unique count
          np  → null_pct
          lc  → True if numeric-but-low-cardinality (treat as label)
        """
        missing = r.get("missing_and_duplicates", {}).get("columns", {})
        out = []
        for col in r.get("schema", {}).get("columns", []):
            raw_dtype  = col.get("dtype", "object")
            short_type = _DTYPE_SHORT.get(raw_dtype, raw_dtype)
            n_unique   = col.get("n_unique", 0)
            is_numeric = short_type in ("int", "float")
            likely_cat = is_numeric and n_unique <= _LOW_CARD_NUMERIC_THRESHOLD
            null_pct   = missing.get(col["name"], {}).get("null_pct", 0)

            entry: dict = {"col": col["name"], "t": short_type, "u": n_unique}
            if null_pct:
                entry["np"] = null_pct
            if likely_cat:
                entry["lc"] = True          # flag only when true
            out.append(entry)
        return out


    def _numeric(self, r: dict, likely_cat_cols: list[str]) -> dict:
        out = {}
        for col, s in r.get("univariate", {}).get("numeric", {}).items():
            if col in likely_cat_cols:
                # Only what matters for label cols (class-imbalance check)
                out[col] = {"lc": 1, "min": s.get("min"), "max": s.get("max"),
                            "z%": s.get("zeros_pct")}
                continue

            v_min, v_max = s.get("min", 0), s.get("max", 0)
            skew = round(s["skewness"], 2)
            entry: dict = {
                "mean":  round(s["mean"], 3),
                "std":   round(s["std"], 3),
                "min":   v_min,
                "max":   v_max,
                "skew":  skew,
                "z%":    s["zeros_pct"],
                "out%":  s["outlier_pct"],
            }
            # only include fields that are non-default / actionable
            null_pct = s.get("null_pct", 0)
            if null_pct:
                entry["np"] = null_pct
            if v_min < 0:
                entry["neg"] = True
            # median only when skewed
            if abs(skew) > 0.5:
                entry["med"] = s["median"]
            out[col] = entry
        return out


    def _categorical(self, r: dict, likely_cat_cols: list[str], full_r: dict) -> dict:
        out: dict = {}

        for col, s in r.get("univariate", {}).get("categorical", {}).items():
            if s["cardinality"] > _ID_CARDINALITY_THRESHOLD and s.get("rare_pct", 0) == 100:
                out[col] = {"card": s["cardinality"], "note": "id"}
                continue

            entry: dict = {"card": s["cardinality"], "mode": s["mode"]}
            top = [f"{v['value']}({v['pct']}%)" for v in s.get("top_values", [])[:_CAT_TOP_N]]
            if top:
                entry["top"] = top
            rare = s.get("rare_pct", 0)
            if rare:
                entry["rare%"] = rare
            out[col] = entry

        # Merge likely_cat numeric columns (brief - rules already in col_roles)
        numeric_stats = full_r.get("univariate", {}).get("numeric", {})
        for col in likely_cat_cols:
            if col in out:
                continue
            s = numeric_stats.get(col, {})
            out[col] = {
                "lc":   True,
                "card": s.get("n_unique"),
                "min":  s.get("min"),
                "max":  s.get("max"),
                "z%":   s.get("zeros_pct"),
            }
        return out


    def _correlations(self, r: dict) -> list[dict]:
        pairs = r.get("correlations", {}).get("top_corr_pairs", [])
        filtered = [
            {"a": p["col_a"], "b": p["col_b"], "r": round(p["value"], 2)}
            for p in pairs
            if abs(p["value"]) >= _CORR_MIN_ABS
        ]
        filtered.sort(key=lambda x: abs(x["r"]), reverse=True)
        return filtered[:_CORR_MAX_PAIRS]

    def _datetime(self, r: dict) -> dict:
        out = {}
        for col, s in r.get("datetime", {}).items():
            out[col] = {k: v for k, v in s.items() if v is not None and k != "timezone"}
        return out

    def _quality(self, r: dict) -> dict:
        dq = r.get("data_quality_score", {})
        return {"score": dq.get("overall_score"), "flags": dq.get("flags", [])}