import math
import pandas as pd
import numpy as np
from typing import Dict, Any


def _safe_float(v) -> float | None:
    if v is None:
        return None
    f = float(v)
    return None if (math.isnan(f) or math.isinf(f)) else f


def univariate_profile(df: pd.DataFrame) -> Dict[str, Any]:
    return {
        "numeric": numeric_stats_handling(df),
        "categorical": categorical_stats_handling(df),
    }


def numeric_stats_handling(df: pd.DataFrame) -> Dict[str, Any]:
    result = {}
    for col in df.select_dtypes(include=np.number).columns:
        s = df[col].replace([np.inf, -np.inf], np.nan).dropna()
        total = len(s) or 1
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = s[(s < lower) | (s > upper)]
        result[col] = {
            "mean": _safe_float(s.mean()),
            "median": _safe_float(s.median()),
            "std": _safe_float(s.std()),
            "min": _safe_float(s.min()),
            "max": _safe_float(s.max()),
            "p25": _safe_float(q1),
            "p75": _safe_float(q3),
            "skewness": _safe_float(s.skew()),
            "kurtosis": _safe_float(s.kurt()),
            "zeros_pct": round(float((s == 0).mean() * 100), 2),
            "outlier_count": int(len(outliers)),
            "outlier_pct": round(len(outliers) / total * 100, 2),
        }
    return result


def categorical_stats_handling(df: pd.DataFrame) -> Dict[str, Any]:
    result = {}
    for col in df.select_dtypes(include=["object", "category"]).columns:
        s = df[col].dropna()
        vc = s.value_counts()
        vc_norm = s.value_counts(normalize=True)
        result[col] = {
            "cardinality": int(s.nunique()),
            "top_values": [
                {"value": k, "count": int(v), "pct": round(vc_norm[k] * 100, 2)}
                for k, v in vc.head(5).items()
            ],
            "entropy": _entropy(s),
            "mode": s.mode().iloc[0] if not s.mode().empty else None,
            "rare_pct": round(float(vc_norm[vc_norm < 0.01].sum() * 100), 2),
        }
    return result


def _entropy(series: pd.Series) -> float:
    probs = series.value_counts(normalize=True)
    return float(-(probs * np.log2(probs + 1e-9)).sum())