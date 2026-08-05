"""Validation helpers for extracted customer data."""
from pathlib import Path
from typing import Sequence
import pandas as pd


def validate_file_exists(path: Path) -> None:
    """Raise ValueError when the expected source file is unavailable."""
    source_path = Path(path)
    if not source_path.is_file():
        raise ValueError(f"Source file does not exist: {source_path}")


def validate_required_columns(
    df: pd.DataFrame, required_columns: Sequence[str],
) -> None:
    """Confirm that data exists and all required columns are present."""
    if df.empty:
        raise ValueError("Customers DataFrame is empty.")
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(
            "Customers DataFrame is missing required columns: "
            + ", ".join(missing_columns)
        )


def validate_primary_key(df: pd.DataFrame, key_column: str) -> None:
    """Confirm that the customer primary key is present, non-null, and unique."""
    if key_column not in df.columns:
        raise ValueError(f"Primary key column is missing: {key_column}")
    if df[key_column].isna().any():
        raise ValueError(f"Primary key column '{key_column}' contains null values.")
    if df[key_column].duplicated().any():
        raise ValueError(f"Primary key column '{key_column}' contains duplicates.")
