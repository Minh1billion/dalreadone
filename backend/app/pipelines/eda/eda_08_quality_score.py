import pandas as pd
import numpy as np
from typing import Dict, Any


def _completeness(df: pd.DataFrame) -> float:
    total_cells = df.size or 1
    missing_cells = int(df.isna().sum().sum())
    return round(1 - missing_cells / total_cells, 4)


def _uniqueness(df: pd.DataFrame) -> float:
    total = len(df) or 1
    duplicates = int(df.duplicated().sum())
    return round(1 - duplicates / total, 4)


def _consistency(df: pd.DataFrame, distributions: Dict[str, Any]) -> float:
    if not distributions:
        return 1.0

    outlier_pcts = [
        v["normality_test"]["p_value"] is not None and
        len(v.get("outlier_rows_idx", [])) / (len(df) or 1)
        for v in distributions.values()
    ]

    avg_outlier_rate = float(np.mean(outlier_pcts)) if outlier_pcts else 0.0
    return round(1 - avg_outlier_rate, 4)


def _timeliness(datetime_profile: Dict[str, Any]) -> float:
    if not datetime_profile:
        return 1.0

    scores = []
    for col_stats in datetime_profile.values():
        gaps = col_stats.get("gaps_count")
        freq = col_stats.get("inferred_freq")
        if gaps is None or freq is None:
            scores.append(1.0)
            continue
        expected = max(col_stats.get("date_range_days", 1), 1)
        scores.append(round(1 - min(gaps / expected, 1.0), 4))

    return round(float(np.mean(scores)), 4) if scores else 1.0


def _build_flags(
    df: pd.DataFrame,
    missing_profile: Dict[str, Any],
    datetime_profile: Dict[str, Any],
) -> list[str]:
    flags = []

    for col, stats in missing_profile.get("columns", {}).items():
        if stats["null_pct"] > 5:
            flags.append(f"high null in '{col}' ({stats['null_pct']}%)")

    if missing_profile.get("duplicate_pct", 0) > 1:
        flags.append(f"duplicate rows: {missing_profile['duplicate_pct']}%")

    for col, stats in datetime_profile.items():
        gaps = stats.get("gaps_count")
        if gaps and gaps > 0:
            flags.append(f"{gaps} datetime gaps in '{col}'")

    return flags


def quality_score(
    df: pd.DataFrame,
    missing_profile: Dict[str, Any],
    datetime_profile: Dict[str, Any],
    distributions: Dict[str, Any],
) -> Dict[str, Any]:
    completeness = _completeness(df)
    uniqueness = _uniqueness(df)
    consistency = _consistency(df, distributions)
    timeliness = _timeliness(datetime_profile)

    overall = round(
        0.35 * completeness +
        0.25 * uniqueness +
        0.25 * consistency +
        0.15 * timeliness,
        4,
    )

    return {
        "completeness": completeness,
        "consistency": consistency,
        "uniqueness": uniqueness,
        "timeliness": timeliness,
        "overall_score": overall,
        "flags": _build_flags(df, missing_profile, datetime_profile),
    }


if __name__ == "__main__":
    import importlib.util
    from pprint import pprint
    from pathlib import Path

    def _load(filename: str):
        p = Path(__file__).parent / filename
        spec = importlib.util.spec_from_file_location(filename, p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    ingest = _load("eda_01_ingest.py")
    missing_mod = _load("eda_03_missing_duplicates.py")
    dt_mod = _load("eda_05_datetime_analysis.py")
    dist_mod = _load("eda_07_distribution_analysis.py")

    df, _ = ingest.read_data("backend\\test\\data.csv")

    missing = missing_mod.missing_duplicates_profile(df)
    dt = dt_mod.datetime_stats_profile(df)
    dist = dist_mod.distribution_profile(df)

    pprint(quality_score(df, missing, dt, dist))