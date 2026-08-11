"""Typed insight and evidence objects."""
from dataclasses import dataclass
from typing import Literal

InsightKind = Literal["trend", "leader", "mix", "risk", "relationship"]
Severity = Literal["positive", "neutral", "warning", "critical", "informational"]


@dataclass(frozen=True)
class Evidence:
    """Traceable values supporting one deterministic observation."""

    current_value: str
    previous_value: str | None = None
    difference: str | None = None
    period: str | None = None
    comparison_period: str | None = None
    sample_size: int | None = None
    source: str = "Validated PostgreSQL analytics"


@dataclass(frozen=True)
class Insight:
    """Structured business observation rendered consistently by the UI."""

    title: str
    message: str
    kind: InsightKind
    severity: Severity
    metric: str
    current_value: float | str | None
    comparison_value: float | str | None = None
    delta: float | None = None
    evidence: Evidence | None = None
    scope: str = "Selected filters"
    supporting_label: str | None = None
    icon: str = "✦"
    priority: float = 0.0

