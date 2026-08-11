"""Consistent product-wide value formatting."""
from typing import Any

import pandas as pd


def compact_number(value: Any, decimals: int = 2) -> str:
    """Format large values with portfolio-friendly K/M/B suffixes."""
    if value is None or pd.isna(value):
        return "—"
    amount = float(value)
    for divisor, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if abs(amount) >= divisor:
            return f"{amount / divisor:.{decimals}f}{suffix}"
    return f"{amount:,.{decimals}f}"


def currency(value: Any, compact: bool = True) -> str:
    """Format Brazilian marketplace currency, compacting large values."""
    if value is None or pd.isna(value):
        return "R$ 0"
    return f"R$ {compact_number(value)}" if compact else f"R$ {float(value):,.2f}"


def number(value: Any, decimals: int = 0, compact: bool = True) -> str:
    """Format a number, compacting values of one thousand or more."""
    if value is None or pd.isna(value):
        return "—"
    amount = float(value)
    if compact and abs(amount) >= 1_000:
        return compact_number(amount, 2)
    return f"{amount:,.{decimals}f}"


def percentage(value: Any) -> str:
    """Format a percentage value."""
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):,.1f}%"
