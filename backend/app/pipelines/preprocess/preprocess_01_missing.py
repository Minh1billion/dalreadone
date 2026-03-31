import pandas as pd
import numpy as np
from typing import Any, Dict, Literal

ImputeStrategy = Literal["mean", "median", "mode", "constant", "drop_row", "drop_col"]


class MissingParams:
    def __init__(
        self,
        num_strategy: ImputeStrategy = "median",
        cat_strategy: ImputeStrategy = "mode",
        num_fill_value: Any = 0,
        cat_fill_value: Any = "unknown",
        drop_col_threshold: float = 0.5,
        drop_row_subset: list[str] | None = None,
        column_overrides: Dict[str, Dict[str, Any]] | None = None,
    ):
        self.num_strategy = num_strategy
        self.cat_strategy = cat_strategy
        self.num_fill_value = num_fill_value
        self.cat_fill_value = cat_fill_value
        self.drop_col_threshold = drop_col_threshold
        self.drop_row_subset = drop_row_subset
        self.column_overrides = column_overrides or {}


def _impute_numeric(series: pd.Series, strategy: ImputeStrategy, fill_value: Any) -> pd.Series:
    if strategy == "mean":
        return series.fillna(series.mean())
    if strategy == "median":
        return series.fillna(series.median())
    if strategy == "mode":
        mode = series.mode()
        return series.fillna(mode.iloc[0] if not mode.empty else fill_value)
    if strategy == "constant":
        return series.fillna(fill_value)
    return series


def _impute_categorical(series: pd.Series, strategy: ImputeStrategy, fill_value: Any) -> pd.Series:
    if strategy == "mode":
        mode = series.mode()
        return series.fillna(mode.iloc[0] if not mode.empty else fill_value)
    if strategy == "constant":
        return series.fillna(fill_value)
    return series


def handle_missing(df: pd.DataFrame, params: MissingParams) -> tuple[pd.DataFrame, Dict[str, Any]]:
    df = df.copy()
    report: Dict[str, Any] = {"columns": {}, "dropped_cols": [], "dropped_rows": 0}

    if params.num_strategy == "drop_row" or params.cat_strategy == "drop_row":
        before = len(df)
        df = df.dropna(subset=params.drop_row_subset)
        report["dropped_rows"] = before - len(df)

    cols_to_drop = []
    for col in df.columns:
        null_pct = df[col].isna().mean()
        override = params.column_overrides.get(col, {})
        is_numeric = pd.api.types.is_numeric_dtype(df[col])

        strategy: ImputeStrategy = override.get(
            "strategy", params.num_strategy if is_numeric else params.cat_strategy
        )
        fill_value = override.get(
            "fill_value", params.num_fill_value if is_numeric else params.cat_fill_value
        )
        drop_threshold = override.get("drop_col_threshold", params.drop_col_threshold)

        col_report: Dict[str, Any] = {
            "null_pct_before": round(null_pct * 100, 2),
            "strategy": strategy,
        }

        if null_pct == 0:
            col_report["action"] = "skip"
        elif null_pct >= drop_threshold:
            col_report["action"] = "drop_col"
            cols_to_drop.append(col)
        elif is_numeric:
            df[col] = _impute_numeric(df[col], strategy, fill_value)
            col_report["action"] = strategy
        else:
            df[col] = _impute_categorical(df[col], strategy, fill_value)
            col_report["action"] = strategy

        report["columns"][col] = col_report

    df.drop(columns=cols_to_drop, inplace=True)
    report["dropped_cols"] = cols_to_drop
    report["rows_after"] = len(df)
    report["cols_after"] = len(df.columns)
    return df, report