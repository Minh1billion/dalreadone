import pandas as pd

TEXT_AVG_CHAR_THRESHOLD = 50
TEXT_COL_RATIO_THRESHOLD = 0.3

def detect_text_columns(df: pd.DataFrame) -> list[str]:
    """return a listed of columns considered as text-heavy."""
    text_cols = []
    for col in df.columns:
        if not pd.api.types.is_object_dtype(df[col]):
            continue
        non_null = df[col].dropna()
        if non_null.empty:
            continue
        
        avg_len = non_null.astype(str).str.len().mean()
        if avg_len >= TEXT_AVG_CHAR_THRESHOLD:
            text_cols.append(col)
            
    return text_cols

def is_text_heavy(df: pd.DataFrame):
    """
    Determine whether a Dataframe is text-heavy.
    
    Returns:
        (True, text_columns) if the dataset is considered text-heavy
        (False, []) if it is standard structured/tabular data
    """
    
    text_cols = detect_text_columns(df)
    ratio = len(text_cols) / len(df.columns) if len(df.columns) > 0 else 0
    heavy = len(text_cols) > 0 and ratio >= TEXT_COL_RATIO_THRESHOLD
    
    if heavy >= TEXT_COL_RATIO_THRESHOLD:
        return heavy, text_cols
    
    return heavy, []
    