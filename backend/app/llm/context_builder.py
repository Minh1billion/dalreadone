import pandas as pd
import io

# Rows of sample data sent to the LLM.
# 3 rows convey data shape well; cutting from 5 saves ~40 tokens per prompt.
_SAMPLE_ROWS = 3

# Max columns included in schema + stats.
# Wide datasets balloon the prompt - keep only the most analysis-relevant columns.
_MAX_SCHEMA_COLS = 20

# Abbreviated dtype names - shorter than pandas default strings
_DTYPE_SHORT: dict[str, str] = {
    "int64": "int", "int32": "int", "int16": "int", "int8": "int",
    "float64": "float", "float32": "float",
    "object": "str", "bool": "bool",
    "datetime64[ns]": "date", "datetime64[ns, UTC]": "date",
    "category": "cat",
}


def _prioritise_columns(df: pd.DataFrame) -> list[str]:
    """
    Return up to _MAX_SCHEMA_COLS column names ordered by analysis usefulness:
      1. numeric  (most useful for aggregations / charts)
      2. datetime (trend analysis)
      3. other    (categorical, text)
    Within each group, original column order is preserved.
    The full df is still used for code execution - LLM code can reference any column.
    """
    numeric   = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    datetimes = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    others    = [c for c in df.columns if c not in numeric and c not in datetimes]
    ordered   = numeric + datetimes + others
    return ordered[:_MAX_SCHEMA_COLS]


def build_dataframe_context(file_bytes: bytes, filename: str) -> dict:
    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))
    else:
        df = pd.read_excel(io.BytesIO(file_bytes))

    cols       = _prioritise_columns(df)
    df_trimmed = df[cols]

    # Schema: one compact line per selected column with abbreviated dtype
    schema_lines = [
        f"- {col} ({_DTYPE_SHORT.get(str(dtype), str(dtype))})"
        for col, dtype in zip(df_trimmed.columns, df_trimmed.dtypes)
    ]
    if len(df.columns) > _MAX_SCHEMA_COLS:
        schema_lines.append(f"... +{len(df.columns) - _MAX_SCHEMA_COLS} more cols")

    # Stats: numeric columns only.
    # Non-numeric top_value lines add ~12 tokens each with low analytical value.
    # Null count omitted when zero to keep lines short.
    stats_lines = []
    for col in df_trimmed.columns:
        if pd.api.types.is_numeric_dtype(df_trimmed[col]):
            null_count = df_trimmed[col].isna().sum()
            line = (
                f"- {col}: min={df_trimmed[col].min()}, "
                f"max={df_trimmed[col].max()}, "
                f"mean={df_trimmed[col].mean():.2f}"
            )
            if null_count > 0:
                line += f", nulls={null_count}"
            stats_lines.append(line)

    return {
        "filename": filename,
        "schema": "\n".join(schema_lines),
        "sample_rows": df_trimmed.head(_SAMPLE_ROWS).to_markdown(index=False),
        "stats": "\n".join(stats_lines),
        # Full df (all columns) passed to code executor - LLM code can use any column
        "df": df,
    }