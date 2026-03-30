import pandas as pd
import numpy as np
from typing import Dict, Any


def is_datetime_column(series: pd.Series, threshold: float = 0.8) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True

    if not pd.api.types.is_object_dtype(series):
        return False

    parsed = pd.to_datetime(series, errors="coerce")
    success_ratio = parsed.notna().mean()

    return success_ratio >= threshold


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
        series = df[col]

        if not is_datetime_column(series):
            continue

        s = pd.to_datetime(series, errors="coerce").dropna().sort_values()

        if s.empty:
            continue

        min_date = s.min()
        max_date = s.max()

        date_range_days = (max_date - min_date).days

        # frequency
        try:
            inferred_freq = pd.infer_freq(s)
        except Exception:
            inferred_freq = None

        # gaps
        if inferred_freq:
            full_range = pd.date_range(start=min_date, end=max_date, freq=inferred_freq)
            gaps_count = len(full_range) - len(s)
        else:
            gaps_count = None

        # seasonality
        seasonality_hint = detect_seasonality(s)

        # timezone
        timezone = str(s.dt.tz) if s.dt.tz is not None else "naive"

        result[col] = {
            "min_date": str(min_date.date()),
            "max_date": str(max_date.date()),
            "date_range_days": int(date_range_days),
            "inferred_freq": inferred_freq,
            "gaps_count": gaps_count,
            "seasonality_hint": seasonality_hint,
            "timezone": timezone,
        }

    return result


if __name__ == "__main__":
    df = pd.read_csv("backend\\test\\data.csv")

    from pprint import pprint
    pprint(datetime_stats_handling(df))