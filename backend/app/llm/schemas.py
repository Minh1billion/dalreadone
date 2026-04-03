from __future__ import annotations
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field


class Severity(str, Enum):
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"


class Priority(str, Enum):
    MUST     = "must"
    SHOULD   = "should"
    OPTIONAL = "optional"


class IssueItem(BaseModel):
    col:      str
    severity: Severity
    detail:   str
    impact:   str


class PrepStep(BaseModel):
    priority:  Priority
    col:       str | None
    action:    str
    rationale: str


class EDAReviewResult(BaseModel):
    overview:      dict
    issues:        list[IssueItem]
    prep_steps:    list[PrepStep]
    opportunities: list[str]       = Field(default_factory=list)
    usage:         dict[str, Any]  = Field(default_factory=dict)


OperationType = Literal["missing", "outlier", "scaling", "encoding"]
StrategyName  = Literal[
    "MeanStrategy", "MedianStrategy", "ModeStrategy",
    "ConstantStrategy", "DropRowStrategy", "DropColStrategy",
    "IQRStrategy", "ZScoreStrategy", "PercentileClipStrategy",
    "MinMaxStrategy", "StandardStrategy", "RobustStrategy",
    "OneHotStrategy", "OrdinalStrategy", "LabelStrategy",
]


class SuggestedLayer(BaseModel):
    operation: OperationType
    strategy:  StrategyName
    cols:      list[str] | None
    params:    dict[str, Any]  = Field(default_factory=dict)
    rationale: str


class CustomLayer(BaseModel):
    operation: Literal["custom"] = "custom"
    cols:      list[str] | None
    code:      str
    rationale: str


class PreprocessSuggestion(BaseModel):
    layers:        list[SuggestedLayer]
    custom_layers: list[CustomLayer]   = Field(default_factory=list)
    usage:         dict[str, Any]      = Field(default_factory=dict)