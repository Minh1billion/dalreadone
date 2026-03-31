import pandas as pd
from typing import Dict, Any


def missing_handling(df: pd.DataFrame, col: str) -> Dict[str, Any] | None:
    series = df[col]
    null_count = int(series.isna().sum())
    if null_count == 0:
        return None
    return {
        "null_count": null_count,
        "null_pct": round(null_count / (len(df) or 1) * 100, 2),
    }


def duplicate_handling(df: pd.DataFrame) -> Dict[str, Any]:
    dup_count = int(df.duplicated().sum())
    return {
        "duplicate_rows": dup_count,
        "duplicate_pct": round(dup_count / (len(df) or 1) * 100, 2),
    }


def missing_duplicates_profile(df: pd.DataFrame) -> Dict[str, Any]:
    return {
        **duplicate_handling(df),
        "columns": {
            col: res
            for col in df.columns
            if (res := missing_handling(df, col)) is not None
        },
    }