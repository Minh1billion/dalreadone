from __future__ import annotations
from enum import Enum
from typing import Any
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
    opportunities: list[str]        = Field(default_factory=list)
    usage:         dict[str, Any]   = Field(default_factory=dict)