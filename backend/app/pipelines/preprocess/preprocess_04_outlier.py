import pandas as pd
import numpy as np
from typing import Dict, Any, Literal

OutlierStrategy = Literal["clip", "winsorize", "drop_row", "impute_median", "skip"]
IQR_MULTIPLIER: float = 1.5


class ColumnOutlierParams:
    def __init__(
        self,
        strategy: OutlierStrategy,
        iqr_k: float = IQR_MULTIPLIER,
        winsorize_bounds: tuple[float, float] = (0.01, 0.99),
    ):
        self.strategy = strategy
        self.iqr_k = iqr_k
        self.winsorize_bounds = winsorize_bounds


class OutlierParams:
    def __init__(
        self,
        default_strategy: OutlierStrategy = "clip",
        iqr_k: float = IQR_MULTIPLIER,
        winsorize_bounds: tuple[float, float] = (0.01, 0.99),
        column_overrides: Dict[str, ColumnOutlierParams] | None = None,
        skip_cols: list[str] | None = None,
    ):
        self.default_strategy = default_strategy
        self.iqr_k = iqr_k
        self.winsorize_bounds = winsorize_bounds
        self.column_overrides = column_overrides or {}
        self.skip_cols = set(skip_cols or [])


def _iqr_fences(series: pd.Series, k: float) -> tuple[float, float]:
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    return float(q1 - k * iqr), float(q3 + k * iqr)


def _outlier_mask(series: pd.Series, lower: float, upper: float) -> pd.Series:
    return (series < lower) | (series > upper)


def _treat_col(df: pd.DataFrame, col: str, col_params: ColumnOutlierParams) -> tuple[pd.DataFrame, Dict[str, Any]]:
    df = df.copy()
    s = df[col].replace([np.inf, -np.inf], np.nan).dropna()
    lower, upper = _iqr_fences(s, col_params.iqr_k)
    mask = _outlier_mask(df[col], lower, upper)
    strategy = col_params.strategy

    col_report: Dict[str, Any] = {
        "col": col,
        "strategy": strategy,
        "fence_lower": round(lower, 4),
        "fence_upper": round(upper, 4),
        "outlier_count_before": int(mask.sum()),
        "outlier_pct_before": round(mask.sum() / (len(df) or 1) * 100, 2),
    }

    if strategy == "clip":
        df[col] = df[col].clip(lower=lower, upper=upper)

    elif strategy == "winsorize":
        lo_p, hi_p = col_params.winsorize_bounds
        lo_v = float(df[col].quantile(lo_p))
        hi_v = float(df[col].quantile(hi_p))
        df[col] = df[col].clip(lower=lo_v, upper=hi_v)
        col_report["winsorize_bounds_values"] = [round(lo_v, 4), round(hi_v, 4)]

    elif strategy == "drop_row":
        before = len(df)
        df = df[~mask | df[col].isna()]
        col_report["rows_dropped"] = before - len(df)

    elif strategy == "impute_median":
        median_val = float(df[col].median())
        df.loc[mask, col] = median_val
        col_report["imputed_with"] = median_val

    col_report["outlier_count_after"] = int(
        _outlier_mask(df[col].replace([np.inf, -np.inf], np.nan), lower, upper).sum()
    )
    return df, col_report


def treat_outliers(df: pd.DataFrame, params: OutlierParams) -> tuple[pd.DataFrame, Dict[str, Any]]:
    df = df.copy()
    report: Dict[str, Any] = {"columns": {}}

    for col in df.select_dtypes(include=np.number).columns.tolist():
        if col in params.skip_cols:
            report["columns"][col] = {"strategy": "skip", "reason": "user_excluded"}
            continue

        if col in params.column_overrides:
            col_params = params.column_overrides[col]
        else:
            col_params = ColumnOutlierParams(
                strategy=params.default_strategy,
                iqr_k=params.iqr_k,
                winsorize_bounds=params.winsorize_bounds,
            )

        df, col_report = _treat_col(df, col, col_params)
        report["columns"][col] = col_report

    report["rows_after"] = len(df)
    report["cols_after"] = len(df.columns)
    return df, report