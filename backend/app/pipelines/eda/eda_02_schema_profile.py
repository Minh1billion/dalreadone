import math
import pandas as pd
from typing import Dict, Any


def _safe_unique(series: pd.Series) -> list:
    result = []
    for v in series.unique().tolist()[:10]:
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            result.append(None)
        else:
            result.append(v)
    return result


def extract_column_schema(df: pd.DataFrame, col: str) -> Dict[str, Any]:
    series = df[col]
    return {
        "name": col,
        "dtype": str(series.dtype),
        "inferred_type": pd.api.types.infer_dtype(series),
        "n_nulls": int(series.isna().sum()),
        "n_unique": int(series.nunique(dropna=True)),
        "first_10_unique_values": _safe_unique(series),
    }


def schema_profile(df: pd.DataFrame) -> Dict[str, Any]:
    return {
        "n_rows": df.shape[0],
        "n_cols": df.shape[1],
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        "columns": [extract_column_schema(df, col) for col in df.columns],
    }