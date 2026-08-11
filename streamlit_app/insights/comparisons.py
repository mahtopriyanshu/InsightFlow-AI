"""Safe comparable-period and delta helpers."""
from dataclasses import dataclass
from datetime import date, timedelta
import math
from typing import Any

from streamlit_app.utils.filters import FilterState


@dataclass(frozen=True)
class ComparisonPeriod:
    current: FilterState
    previous: FilterState | None
    available: bool
    reason: str | None = None


def previous_comparable_period(
    filters: FilterState,
    available_start: date,
) -> ComparisonPeriod:
    """Return an equal inclusive period immediately before the selection."""
    duration = (filters.end_date - filters.start_date).days + 1
    if duration <= 0:
        return ComparisonPeriod(filters, None, False, "Invalid selected period")
    previous_end = filters.start_date - timedelta(days=1)
    previous_start = previous_end - timedelta(days=duration - 1)
    if previous_start < available_start:
        return ComparisonPeriod(
            filters, None, False,
            "The dataset does not contain a complete previous comparable period.",
        )
    previous = FilterState(
        previous_start, previous_end, filters.states, filters.categories
    )
    return ComparisonPeriod(filters, previous, True)


def safe_float(value: Any) -> float | None:
    """Convert numeric-like values while rejecting null and non-finite data."""
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def absolute_change(current: Any, previous: Any) -> float | None:
    current_value, previous_value = safe_float(current), safe_float(previous)
    if current_value is None or previous_value is None:
        return None
    return current_value - previous_value


def percentage_change(current: Any, previous: Any) -> float | None:
    current_value, previous_value = safe_float(current), safe_float(previous)
    if current_value is None or previous_value is None or previous_value == 0:
        return None
    return 100.0 * (current_value - previous_value) / abs(previous_value)


def percentage_point_change(current: Any, previous: Any) -> float | None:
    """Rates are already represented as percentages, so subtraction yields pp."""
    return absolute_change(current, previous)


def period_label(filters: FilterState) -> str:
    return f"{filters.start_date:%d %b %Y} – {filters.end_date:%d %b %Y}"


def scope_label(filters: FilterState) -> str:
    parts = []
    if filters.states:
        parts.append(f"state: {', '.join(filters.states)}")
    if filters.categories:
        parts.append(f"category: {', '.join(filters.categories)}")
    return " · ".join(parts) if parts else "All selected marketplace data"

