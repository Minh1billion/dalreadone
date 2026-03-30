import pandas as pd
from typing import Dict, Any


def extract_column_schema(df: pd.DataFrame, col: str) -> Dict[str, Any]:
    series = df[col]

    return {
        "name": col,
        "dtype": str(series.dtype),
        "inferred_type": pd.api.types.infer_dtype(series),
        "n_nulls": int(series.isna().sum()),
        "n_unique": int(series.nunique(dropna=True)),
        "first_10_unique_values": series.unique().tolist()[:10],
    }


def schema_profile(df: pd.DataFrame) -> Dict[str, Any]:
    columns = [extract_column_schema(df, col) for col in df.columns]

    schema = {
        "n_rows": df.shape[0],
        "n_cols": df.shape[1],
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        "columns": columns,
    }

    return schema


if __name__ == "__main__":
    df = pd.read_csv("backend\\test\\data.csv")

    result = schema_profile(df)

    from pprint import pprint
    pprint(result)