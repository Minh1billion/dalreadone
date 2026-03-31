import pandas as pd
import numpy as np
from typing import Dict, Any, Literal

EncodeStrategy = Literal["onehot", "ordinal", "binary", "frequency", "skip"]


class ColumnEncodeParams:
    def __init__(
        self,
        strategy: EncodeStrategy,
        ordinal_categories: list | None = None,
        max_onehot_cardinality: int = 20,
    ):
        self.strategy = strategy
        self.ordinal_categories = ordinal_categories
        self.max_onehot_cardinality = max_onehot_cardinality


class EncodingParams:
    def __init__(
        self,
        default_strategy: EncodeStrategy = "onehot",
        max_onehot_cardinality: int = 20,
        column_overrides: Dict[str, ColumnEncodeParams] | None = None,
        skip_cols: list[str] | None = None,
    ):
        self.default_strategy = default_strategy
        self.max_onehot_cardinality = max_onehot_cardinality
        self.column_overrides = column_overrides or {}
        self.skip_cols = set(skip_cols or [])


def _auto_strategy(series: pd.Series, max_onehot: int) -> EncodeStrategy:
    n = series.nunique(dropna=True)
    if n <= 1:
        return "skip"
    if n == 2:
        return "binary"
    if n <= max_onehot:
        return "onehot"
    return "frequency"


def _onehot(df: pd.DataFrame, col: str) -> tuple[pd.DataFrame, list[str]]:
    dummies = pd.get_dummies(df[col], prefix=col, drop_first=False, dtype=np.uint8)
    new_cols = dummies.columns.tolist()
    return pd.concat([df.drop(columns=[col]), dummies], axis=1), new_cols


def _ordinal(df: pd.DataFrame, col: str, categories: list | None) -> pd.DataFrame:
    if categories:
        cat_type = pd.CategoricalDtype(categories=categories, ordered=True)
        df[col] = df[col].astype(cat_type).cat.codes.replace(-1, np.nan)
    else:
        df[col] = df[col].astype("category").cat.codes.replace(-1, np.nan)
    return df


def _binary(df: pd.DataFrame, col: str) -> pd.DataFrame:
    vc = df[col].value_counts()
    mapping = {vc.index[0]: 0, vc.index[1]: 1} if len(vc) >= 2 else {vc.index[0]: 0}
    df[col] = df[col].map(mapping)
    return df


def _frequency(df: pd.DataFrame, col: str) -> pd.DataFrame:
    freq_map = df[col].value_counts(normalize=True).to_dict()
    df[col] = df[col].map(freq_map)
    return df


def _encode_col(
    df: pd.DataFrame,
    col: str,
    col_params: ColumnEncodeParams,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    strategy = col_params.strategy
    new_cols: list[str] | None = None

    if strategy == "onehot":
        df, new_cols = _onehot(df, col)
    elif strategy == "ordinal":
        df = _ordinal(df, col, col_params.ordinal_categories)
    elif strategy == "binary":
        df = _binary(df, col)
    elif strategy == "frequency":
        df = _frequency(df, col)

    return df, {
        "col": col,
        "strategy": strategy,
        "new_cols": new_cols or ([col] if col in df.columns else []),
    }


def encode_categoricals(df: pd.DataFrame, params: EncodingParams) -> tuple[pd.DataFrame, Dict[str, Any]]:
    df = df.copy()
    report: Dict[str, Any] = {"columns": {}}

    for col in df.select_dtypes(include=["object", "category"]).columns.tolist():
        if col in params.skip_cols:
            report["columns"][col] = {"strategy": "skip", "reason": "user_excluded"}
            continue

        if col in params.column_overrides:
            col_params = params.column_overrides[col]
        else:
            strategy = _auto_strategy(df[col], params.max_onehot_cardinality)
            if strategy == "skip" and params.default_strategy != "skip":
                strategy = params.default_strategy
            col_params = ColumnEncodeParams(
                strategy=strategy,
                max_onehot_cardinality=params.max_onehot_cardinality,
            )

        df, col_report = _encode_col(df, col, col_params)
        report["columns"][col] = col_report

    report["cols_after"] = len(df.columns)
    return df, report