import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Literal

import numpy as np
import pandas as pd

from app.pipelines.preprocess import (
    preprocess_01_missing as m01,
    preprocess_02_encoding as m02,
    preprocess_03_scaling as m03,
    preprocess_04_outlier as m04,
)

StepName = Literal["missing", "encoding", "outlier", "scaling"]


@dataclass
class MissingStep:
    name: Literal["missing"] = "missing"
    params: m01.MissingParams = field(default_factory=m01.MissingParams)


@dataclass
class EncodingStep:
    name: Literal["encoding"] = "encoding"
    params: m02.EncodingParams = field(default_factory=m02.EncodingParams)


@dataclass
class OutlierStep:
    name: Literal["outlier"] = "outlier"
    params: m04.OutlierParams = field(default_factory=m04.OutlierParams)


@dataclass
class ScalingStep:
    name: Literal["scaling"] = "scaling"
    params: m03.ScalingParams = field(default_factory=m03.ScalingParams)


PipelineStep = MissingStep | EncodingStep | OutlierStep | ScalingStep

DEFAULT_PIPELINE: list[PipelineStep] = [
    MissingStep(),
    EncodingStep(),
    OutlierStep(),
    ScalingStep(),
]

_STEP_PROGRESS: Dict[StepName, int] = {
    "missing": 15,
    "encoding": 38,
    "outlier": 62,
    "scaling": 85,
}

_RUNNERS = {
    "missing":  lambda df, step: m01.handle_missing(df, step.params),
    "encoding": lambda df, step: m02.encode_categoricals(df, step.params),
    "outlier":  lambda df, step: m04.treat_outliers(df, step.params),
    "scaling":  lambda df, step: m03.scale_numerics(df, step.params),
}


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


def run_preprocess(
    df: pd.DataFrame,
    source: str = "unknown",
    steps: list[PipelineStep] | None = None,
    on_step: Callable[[str, int], None] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    steps = steps if steps is not None else DEFAULT_PIPELINE
    step_reports: Dict[str, Any] = {}

    for step in steps:
        if on_step:
            on_step(step.name, _STEP_PROGRESS.get(step.name, 0))
        runner = _RUNNERS[step.name]
        df, step_report = runner(df, step)
        step_reports[step.name] = step_report

    if on_step:
        on_step("done", 100)

    report = sanitize_for_json({
        "preprocess_report": {
            "meta": {
                "source_file": source,
                "generated_at": pd.Timestamp.utcnow().isoformat(),
                "steps_executed": [s.name for s in steps],
                "rows_out": len(df),
                "cols_out": len(df.columns),
            },
            **step_reports,
        }
    })

    return df, report