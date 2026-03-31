import pandas as pd
import numpy as np
from typing import Dict, Any
from scipy.stats import shapiro


def normality_test(series: pd.Series) -> Dict[str, Any]:
    s = series.dropna()
    if len(s) < 3:
        return {"method": "shapiro", "p_value": None, "is_normal": None}
    if len(s) > 5000:
        s = s.sample(5000, random_state=42)
    _, p = shapiro(s)
    return {
        "method": "shapiro",
        "p_value": round(float(p), 5),
        "is_normal": bool(p > 0.05),
    }


def dist_type_hint(series: pd.Series) -> str:
    skew = series.skew()
    if skew > 0.5:
        return "right-skewed"
    if skew < -0.5:
        return "left-skewed"
    return "approximately-normal"


def histogram_bins(series: pd.Series, bins: int = 10) -> list:
    counts, edges = np.histogram(series.dropna(), bins=bins)
    return [
        {"range": f"[{round(edges[i], 2)},{round(edges[i+1], 2)})", "count": int(counts[i])}
        for i in range(len(counts))
    ]


def outlier_summary(series: pd.Series, preview_n: int = 10) -> Dict[str, Any]:
    s = series.dropna()
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    mask = (series < lower) | (series > upper)
    return {
        "count": int(mask.sum()),
        "pct": round(float(mask.sum() / (len(s) or 1) * 100), 2),
        "lower_fence": round(float(lower), 4),
        "upper_fence": round(float(upper), 4),
        "preview_idx": series[mask].index[:preview_n].tolist(),
    }


def distribution_profile(df: pd.DataFrame) -> Dict[str, Any]:
    result = {}
    for col in df.select_dtypes(include=np.number).columns:
        s = df[col].replace([np.inf, -np.inf], np.nan).dropna()
        if s.empty:
            continue
        result[col] = {
            "normality_test": normality_test(s),
            "dist_type_hint": dist_type_hint(s),
            "histogram_bins": histogram_bins(s),
            "outlier_summary": outlier_summary(s),
        }
    return result