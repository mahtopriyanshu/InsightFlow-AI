"""Pure presentation helpers for the governed Assistant UI."""
from dataclasses import dataclass

import pandas as pd

from streamlit_app.assistant.models import (
    AssistantUnavailable,
    NoDataError,
    QueryTimeoutError,
    SQLValidationError,
    SafeExecutionError,
    UnsafeQuestion,
    UnsupportedQuestion,
)


@dataclass(frozen=True)
class FriendlyStatus:
    message: str
    kind: str
    retryable: bool = False


def humanize_label(value: str) -> str:
    overrides = {
        "aov": "Average Order Value",
        "late_delivery_rate": "Late-Delivery Rate",
        "payment_revenue": "Payment Revenue",
        "merchandise_revenue": "Merchandise Revenue",
    }
    return overrides.get(str(value), str(value).replace("_", " ").strip().title())


def humanize_entity(value):
    if not isinstance(value, str):
        return value
    return value.replace("_", " ").strip().title()


def prepare_display_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a display-only copy; the verified answer frame remains untouched."""
    display = frame.copy()
    for column in ("category", "payment_type"):
        if column in display.columns:
            display[column] = display[column].map(humanize_entity)
    return display.rename(columns={column: humanize_label(column) for column in display.columns})


def friendly_status(error: Exception) -> FriendlyStatus:
    if isinstance(error, AssistantUnavailable):
        return FriendlyStatus("AI planning is temporarily unavailable. Your previous conversation is safe. You can retry this question.", "provider", True)
    if isinstance(error, UnsafeQuestion):
        return FriendlyStatus("This request cannot be executed because it falls outside the assistant's read-only analytics capabilities.", "security")
    if isinstance(error, UnsupportedQuestion):
        if "causal" in str(error).lower():
            return FriendlyStatus("Causal explanations are not supported by this observational dataset. Ask for a comparison or observed contributors instead.", "causal")
        return FriendlyStatus("This analysis is not currently supported by the governed assistant. Try asking about sales, customers, products, sellers, delivery, reviews, or payments.", "unsupported")
    if isinstance(error, NoDataError):
        return FriendlyStatus("No matching data was found for the current filter scope.", "no_data")
    if isinstance(error, QueryTimeoutError):
        return FriendlyStatus("The analysis could not be completed within the safe query limit. Try narrowing the filters or simplifying the question.", "timeout")
    if isinstance(error, (SQLValidationError, SafeExecutionError)):
        return FriendlyStatus("The analysis could not be completed safely. Try simplifying the question or adjusting the filters.", "execution")
    return FriendlyStatus("The analysis could not be completed safely. Please try a supported business question.", "execution")
