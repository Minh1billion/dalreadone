import pandas as pd
import numpy as np
from typing import Dict, Any


def _completeness(df: pd.DataFrame) -> float:
    return round(1 - df.isna().sum().sum() / (df.size or 1), 4)


def _uniqueness(df: pd.DataFrame) -> float:
    return round(1 - df.duplicated().sum() / (len(df) or 1), 4)


def _consistency(df: pd.DataFrame, distributions: Dict[str, Any]) -> float:
    if not distributions:
        return 1.0
    rates = [
        v["outlier_summary"]["count"] / (len(df) or 1)
        for v in distributions.values()
        if "outlier_summary" in v
    ]
    return round(1 - float(np.mean(rates)), 4) if rates else 1.0


def _timeliness(datetime_profile: Dict[str, Any]) -> float:
    if not datetime_profile:
        return 1.0
    scores = []
    for stats in datetime_profile.values():
        gaps = stats.get("gaps_count")
        freq = stats.get("inferred_freq")
        if gaps is None or freq is None:
            scores.append(1.0)
            continue
        expected = max(stats.get("date_range_days", 1), 1)
        scores.append(round(1 - min(gaps / expected, 1.0), 4))
    return round(float(np.mean(scores)), 4) if scores else 1.0


def _build_flags(missing_profile: Dict[str, Any], datetime_profile: Dict[str, Any]) -> list[str]:
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
        0.35 * completeness + 0.25 * uniqueness + 0.25 * consistency + 0.15 * timeliness, 4
    )
    return {
        "completeness": completeness,
        "consistency": consistency,
        "uniqueness": uniqueness,
        "timeliness": timeliness,
        "overall_score": overall,
        "flags": _build_flags(missing_profile, datetime_profile),
    }