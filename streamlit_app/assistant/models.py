"""Typed contracts for the governed business analyst."""
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

import pandas as pd


ChartType = Literal["kpi", "bar", "line", "donut", "table"]
RankingDirection = Literal["ascending", "descending", "none"]


@dataclass(frozen=True)
class QueryMetadata:
    metric: str
    dimension: str
    chart_type: ChartType
    ranking_direction: RankingDirection = "none"
    time_grain: str | None = None


@dataclass(frozen=True)
class IntentPlan:
    intent: str
    limit: int = 10
    states: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    start_date: date | None = None
    end_date: date | None = None
    interpretation: str = ""
    metadata: QueryMetadata | None = None


@dataclass(frozen=True)
class GeneratedQuery:
    sql: str
    params: tuple[object, ...]
    metric_key: str
    metadata: QueryMetadata
    source: str = "olist_analytics serving layer with validated CTE fallback"


@dataclass(frozen=True)
class AnswerEvidence:
    source: str
    metric_definition: str
    effective_scope: str
    execution_ms: float
    row_count: int
    llm_calls: int


@dataclass
class AssistantAnswer:
    question: str
    intent: str
    interpretation: str
    scope: str
    sql: str
    params: tuple[object, ...]
    data: pd.DataFrame
    message: str
    metadata: QueryMetadata
    evidence: AnswerEvidence
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def chart_type(self) -> ChartType:
        return self.metadata.chart_type


class AssistantError(Exception):
    """Safe user-facing assistant failure."""


class AssistantUnavailable(AssistantError):
    """Raised when no configured provider can interpret questions."""


class UnsupportedQuestion(AssistantError):
    """Raised when the approved semantic layer cannot answer a question."""


class UnsafeQuestion(AssistantError):
    """Raised for adversarial or unsafe instructions."""


class SQLValidationError(AssistantError):
    """Raised when a query fails structural governance."""


class NoDataError(AssistantError):
    """Raised when the governed query has no rows in the effective scope."""


class QueryTimeoutError(AssistantError):
    """Raised when PostgreSQL stops a query at the governed timeout."""


class SafeExecutionError(AssistantError):
    """Raised when a read-only query cannot be completed safely."""
