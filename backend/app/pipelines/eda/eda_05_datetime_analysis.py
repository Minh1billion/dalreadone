import pandas as pd
from typing import Dict, Any


def is_datetime_column(series: pd.Series, threshold: float = 0.8) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    if not pd.api.types.is_object_dtype(series):
        return False
    parsed = pd.to_datetime(series, errors="coerce", format="mixed", dayfirst=False)
    return parsed.notna().mean() >= threshold


def detect_seasonality(series: pd.Series) -> str:
    if len(series) < 10:
        return "unknown"
    diffs = series.sort_values().diff().dropna()
    if diffs.empty:
        return "unknown"
    mode_days = diffs.dt.days.mode()
    if mode_days.empty:
        return "unknown"
    d = mode_days.iloc[0]
    if d == 1:
        return "daily"
    if d == 7:
        return "weekly"
    if d in [28, 29, 30, 31]:
        return "monthly"
    return "unknown"


def datetime_stats_profile(df: pd.DataFrame) -> Dict[str, Any]:
    result = {}
    for col in df.columns:
        if not is_datetime_column(df[col]):
            continue
        s = pd.to_datetime(df[col], errors="coerce").dropna().sort_values()
        if s.empty:
            continue
        min_date, max_date = s.min(), s.max()
        try:
            inferred_freq = pd.infer_freq(s)
        except Exception:
            inferred_freq = None
        if inferred_freq:
            full_range = pd.date_range(start=min_date, end=max_date, freq=inferred_freq)
            gaps_count = len(full_range) - len(s)
        else:
            gaps_count = None
        result[col] = {
            "min_date": str(min_date.date()),
            "max_date": str(max_date.date()),
            "date_range_days": int((max_date - min_date).days),
            "inferred_freq": inferred_freq,
            "gaps_count": gaps_count,
            "seasonality_hint": detect_seasonality(s),
            "timezone": str(s.dt.tz) if s.dt.tz is not None else "naive",
        }
    return result