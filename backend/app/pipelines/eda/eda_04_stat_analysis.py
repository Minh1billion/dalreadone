import pandas as pd
import numpy as np
from typing import Dict, Any


def univariate_profile(df: pd.DataFrame) -> Dict[str, Any]:
    return {
        "numeric": numeric_stats_handling(df),
        "categorical": categorical_stats_handling(df),
    }


def numeric_stats_handling(df: pd.DataFrame) -> Dict[str, Any]:
    result = {}

    numeric_cols = df.select_dtypes(include=np.number).columns

    for col in numeric_cols:
        s = df[col].dropna()
        total = len(s) or 1

        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1

        # IQR outlier
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = s[(s < lower) | (s > upper)]

        result[col] = {
            "mean": float(s.mean()),
            "median": float(s.median()),
            "std": float(s.std()),
            "min": float(s.min()),
            "max": float(s.max()),
            "p25": float(q1),
            "p75": float(q3),
            "skewness": float(s.skew()),
            "kurtosis": float(s.kurt()),
            "zeros_pct": round((s == 0).mean() * 100, 2),
            "outlier_count": int(len(outliers)),
            "outlier_pct": round(len(outliers) / total * 100, 2),
        }

    return result


def categorical_stats_handling(df: pd.DataFrame) -> Dict[str, Any]:
    result = {}

    cat_cols = df.select_dtypes(include=["object", "category"]).columns

    for col in cat_cols:
        s = df[col].dropna()
        total = len(s) or 1

        vc = s.value_counts()
        vc_norm = s.value_counts(normalize=True)

        top_values = [
            {
                "value": k,
                "count": int(v),
                "pct": round(vc_norm[k] * 100, 2),
            }
            for k, v in vc.head(5).items()
        ]

        rare_pct = round((vc_norm[vc_norm < 0.01].sum()) * 100, 2)

        result[col] = {
            "cardinality": int(s.nunique()),
            "top_values": top_values,
            "entropy": _entropy(s),
            "mode": s.mode().iloc[0] if not s.mode().empty else None,
            "rare_pct": rare_pct,
        }

    return result

def _entropy(series: pd.Series) -> float:
    probs = series.value_counts(normalize=True)
    return float(-(probs * np.log2(probs + 1e-9)).sum())

if __name__ == "__main__":
    df = pd.read_csv("backend\\test\\data.csv")

    from pprint import pprint
    pprint(univariate_profile(df))