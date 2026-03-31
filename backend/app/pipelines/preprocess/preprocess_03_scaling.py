import pandas as pd
import numpy as np
from typing import Dict, Any, Literal

ScaleStrategy = Literal["standard", "minmax", "robust", "log1p", "skip"]
HIGH_SKEW_THRESHOLD: float = 1.0


class ColumnScaleParams:
    def __init__(
        self,
        strategy: ScaleStrategy,
        feature_range: tuple[float, float] = (0.0, 1.0),
    ):
        self.strategy = strategy
        self.feature_range = feature_range


class ScalingParams:
    def __init__(
        self,
        default_strategy: ScaleStrategy = "standard",
        feature_range: tuple[float, float] = (0.0, 1.0),
        column_overrides: Dict[str, ColumnScaleParams] | None = None,
        skip_cols: list[str] | None = None,
    ):
        self.default_strategy = default_strategy
        self.feature_range = feature_range
        self.column_overrides = column_overrides or {}
        self.skip_cols = set(skip_cols or [])


def _auto_strategy(series: pd.Series) -> ScaleStrategy:
    if series.min() > 0 and abs(series.skew()) >= HIGH_SKEW_THRESHOLD:
        return "log1p"
    return "standard"


def _standard(series: pd.Series) -> tuple[pd.Series, Dict[str, float]]:
    mean, std = float(series.mean()), float(series.std())
    std = std or 1.0
    return (series - mean) / std, {"mean": mean, "std": std}


def _minmax(series: pd.Series, lo: float, hi: float) -> tuple[pd.Series, Dict[str, float]]:
    mn, mx = float(series.min()), float(series.max())
    rng = mx - mn or 1.0
    return (series - mn) / rng * (hi - lo) + lo, {"min": mn, "max": mx, "range_lo": lo, "range_hi": hi}


def _robust(series: pd.Series) -> tuple[pd.Series, Dict[str, float]]:
    q1, q3 = float(series.quantile(0.25)), float(series.quantile(0.75))
    median = float(series.median())
    iqr = q3 - q1 or 1.0
    return (series - median) / iqr, {"median": median, "iqr": iqr}


def _log1p(series: pd.Series) -> tuple[pd.Series, Dict[str, Any]]:
    shift = abs(series.min()) + 1 if series.min() < 0 else 0
    return np.log1p(series + shift), {"shift": shift}


def _scale_col(df: pd.DataFrame, col: str, col_params: ColumnScaleParams) -> tuple[pd.DataFrame, Dict[str, Any]]:
    df = df.copy()
    s = df[col].replace([np.inf, -np.inf], np.nan)
    clean = s.dropna()
    strategy = col_params.strategy
    fit_params: Dict[str, Any] = {}

    if strategy == "standard":
        scaled, fit_params = _standard(clean)
    elif strategy == "minmax":
        lo, hi = col_params.feature_range
        scaled, fit_params = _minmax(clean, lo, hi)
    elif strategy == "robust":
        scaled, fit_params = _robust(clean)
    elif strategy == "log1p":
        scaled, fit_params = _log1p(clean)
    else:
        return df, {"col": col, "strategy": "skip"}

    df[col] = s.where(s.isna(), scaled)
    return df, {"col": col, "strategy": strategy, "fit_params": fit_params}


def scale_numerics(df: pd.DataFrame, params: ScalingParams) -> tuple[pd.DataFrame, Dict[str, Any]]:
    df = df.copy()
    report: Dict[str, Any] = {"columns": {}}

    for col in df.select_dtypes(include=np.number).columns.tolist():
        if col in params.skip_cols:
            report["columns"][col] = {"strategy": "skip", "reason": "user_excluded"}
            continue

        if col in params.column_overrides:
            col_params = params.column_overrides[col]
        else:
            strategy = params.default_strategy
            if strategy == "auto":
                strategy = _auto_strategy(df[col].replace([np.inf, -np.inf], np.nan).dropna())
            col_params = ColumnScaleParams(strategy=strategy, feature_range=params.feature_range)

        df, col_report = _scale_col(df, col, col_params)
        report["columns"][col] = col_report

    report["cols_scaled"] = sum(1 for v in report["columns"].values() if v.get("strategy") != "skip")
    return df, report