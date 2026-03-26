import pandas as pd
import io

def build_dataframe_context(file_bytes: bytes, filename: str) -> dict:
    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))
    else:
        df = pd.read_excel(io.BytesIO(file_bytes))

    schema_lines = [f"- {col} ({dtype})" for col, dtype in zip(df.columns, df.dtypes)]

    stats_lines = []
    for col in df.columns:
        null_count = df[col].isna().sum()
        if pd.api.types.is_numeric_dtype(df[col]):
            stats_lines.append(
                f"- {col}: min={df[col].min()}, max={df[col].max()}, "
                f"mean={df[col].mean():.2f}, nulls={null_count}"
            )
        else:
            # guard against all-null columns before calling value_counts()
            if df[col].notna().any():
                top = df[col].value_counts().index[0]
            else:
                top = "N/A"
            stats_lines.append(f"- {col}: top_value={top}, nulls={null_count}")

    return {
        "filename": filename,
        "schema": "\n".join(schema_lines),
        "sample_rows": df.head(5).to_markdown(index=False),
        "stats": "\n".join(stats_lines),
        "df": df,
    }