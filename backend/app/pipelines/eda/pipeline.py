import json
import importlib.util
from pathlib import Path
from typing import Any, Callable

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

def _load(filename: str):
    p = Path(__file__).parent / filename
    spec = importlib.util.spec_from_file_location(filename, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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

    report = {
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
    }

    if output_path:
        Path(output_path).write_text(json.dumps(report, indent=2, default=str))

    return report


if __name__ == "__main__":
    import sys
    from app.pipelines.eda.eda_01_ingest import read_data

    data_path = sys.argv[1] if len(sys.argv) > 1 else "test\\data.csv"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "test\\eda_report_sample.json"

    df, meta = read_data(data_path)
    run_eda(df, source=meta["source"], output_path=output_path)