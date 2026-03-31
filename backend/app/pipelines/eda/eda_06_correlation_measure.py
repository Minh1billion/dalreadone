import pandas as pd
import numpy as np
from typing import Dict, Any
from itertools import combinations

from scipy.stats import chi2_contingency


MAX_CARDINALITY = 50
SAMPLE_SIZE = 100_000
RANDOM_SEED = 42


def pearson_correlation(df: pd.DataFrame) -> Dict[str, float]:
    result = {}

    num_df = df.select_dtypes(include=np.number).dropna(how="all")
    if num_df.shape[1] < 2:
        return result

    arr = num_df.values.astype(np.float64)
    cols = num_df.columns.tolist()

    col_means = np.nanmean(arr, axis=0)
    nan_mask = np.isnan(arr)
    arr[nan_mask] = np.take(col_means, np.where(nan_mask)[1])

    corr_matrix = np.corrcoef(arr, rowvar=False)

    for i, j in combinations(range(len(cols)), 2):
        key = f"{cols[i]}__{cols[j]}"
        val = corr_matrix[i, j]
        result[key] = round(float(val), 4) if not np.isnan(val) else 0.0

    return result


def cramers_v(x: pd.Series, y: pd.Series) -> float:
    if len(x) > SAMPLE_SIZE:
        idx = np.random.choice(len(x), SAMPLE_SIZE, replace=False)
        x, y = x.iloc[idx], y.iloc[idx]

    confusion_matrix = pd.crosstab(x, y)
    if confusion_matrix.size == 0:
        return 0.0

    n = confusion_matrix.values.sum()
    if n == 0:
        return 0.0

    r, k = confusion_matrix.shape
    denom = min(k - 1, r - 1)
    if denom == 0:
        return 0.0

    chi2, _, _, _ = chi2_contingency(confusion_matrix, correction=False)

    return float(np.sqrt(chi2 / (n * denom)))


def categorical_correlation(df: pd.DataFrame) -> Dict[str, float]:
    result = {}

    cat_df = df.select_dtypes(include=["object", "category"])
    if cat_df.shape[1] < 2:
        return result

    low_card_cols = [
        col for col in cat_df.columns
        if cat_df[col].nunique() <= MAX_CARDINALITY
    ]

    if len(low_card_cols) < 2:
        return result

    cat_df = cat_df[low_card_cols]

    for col_a, col_b in combinations(cat_df.columns, 2):
        pair = cat_df[[col_a, col_b]].dropna()
        if pair.empty:
            continue
        value = cramers_v(pair[col_a], pair[col_b])
        key = f"{col_a}__{col_b}"
        result[key] = round(value, 4)

    return result


def get_top_corr_pairs(
    pearson: Dict[str, float],
    cramers: Dict[str, float],
    top_n: int = 5,
) -> list:
    pairs = []

    for k, v in pearson.items():
        col_a, col_b = k.split("__", 1)
        pairs.append({"col_a": col_a, "col_b": col_b, "method": "pearson", "value": v})

    for k, v in cramers.items():
        col_a, col_b = k.split("__", 1)
        pairs.append({"col_a": col_a, "col_b": col_b, "method": "cramers_v", "value": v})

    pairs.sort(key=lambda x: abs(x["value"]), reverse=True)
    return pairs[:top_n]


def _sample_df(df: pd.DataFrame, n: int, seed: int = RANDOM_SEED) -> pd.DataFrame:
    if len(df) <= n:
        return df
    return df.sample(n=n, random_state=seed).reset_index(drop=True)


def correlation_profile(df: pd.DataFrame) -> Dict[str, Any]:
    df_sampled = _sample_df(df, SAMPLE_SIZE, RANDOM_SEED)
    
    pearson = pearson_correlation(df_sampled)
    cramers = categorical_correlation(df_sampled)

    return {
        "pearson": pearson,
        "cramers_v": cramers,
        "top_corr_pairs": get_top_corr_pairs(pearson, cramers),
    }


if __name__ == "__main__":
    df = pd.read_csv("backend\\test\\data.csv")

    from pprint import pprint
    pprint(correlation_profile(df))