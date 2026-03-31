import json
import math
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from app.pipelines.eda import (
    eda_02_schema_profile as m02,
    eda_03_missing_duplicates as m03,
    eda_04_stat_analysis as m04,
    eda_05_datetime_analysis as m05,
    eda_06_correlation_measure as m06,
    eda_07_distribution_analysis as m07,
    eda_08_quality_score as m08,
)


def sanitize_for_json(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, np.floating):
        f = float(obj)
        return None if (math.isnan(f) or math.isinf(f)) else f
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    return obj


def run_eda(
    df: pd.DataFrame,
    source: str = "unknown",
    output_path: str | None = None,
    on_step: Callable[[str, int], None] | None = None,
) -> dict[str, Any]:

    def _step(name: str, progress: int):
        if on_step:
            on_step(name, progress)

    _step("schema", 10)
    schema = m02.schema_profile(df)

    _step("missing_and_duplicates", 25)
    missing = m03.missing_duplicates_profile(df)

    _step("univariate", 38)
    univariate = m04.univariate_profile(df)

    _step("datetime", 52)
    dt = m05.datetime_stats_profile(df)

    _step("correlations", 65)
    correlations = m06.correlation_profile(df)

    _step("distributions", 80)
    dist = m07.distribution_profile(df)

    _step("data_quality_score", 95)
    quality = m08.quality_score(df, missing, dt, dist)

    report = sanitize_for_json({
        "eda_report": {
            "meta": {
                "source_file": source,
                "generated_at": pd.Timestamp.utcnow().isoformat(),
            },
            "schema": schema,
            "missing_and_duplicates": missing,
            "univariate": univariate,
            "datetime": dt,
            "correlations": correlations,
            "distributions": dist,
            "data_quality_score": quality,
        }
    })

    if output_path:
        Path(output_path).write_text(json.dumps(report, indent=2))

    return report