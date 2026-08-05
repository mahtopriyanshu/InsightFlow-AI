"""Validation helpers for extracted Olist data."""
from pathlib import Path
from typing import Sequence

import pandas as pd


def validate_file_exists(path: Path) -> None:
    """Raise ValueError when the expected source file is unavailable."""
    source_path = Path(path)
    if not source_path.is_file():
        raise ValueError(f"Source file does not exist: {source_path}")


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: Sequence[str],
) -> None:
    """Confirm that data exists and all required columns are present."""
    if df.empty:
        raise ValueError("DataFrame is empty.")
    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(
            "DataFrame is missing required columns: " + ", ".join(missing_columns)
        )


def validate_primary_key(
    df: pd.DataFrame,
    key_columns: str | Sequence[str],
) -> None:
    """Confirm that a scalar or composite primary key is present and unique."""
    columns = [key_columns] if isinstance(key_columns, str) else list(key_columns)
    if not columns:
        raise ValueError("At least one primary key column is required.")

    missing_columns = [column for column in columns if column not in df.columns]
    if missing_columns:
        raise ValueError(
            "Primary key columns are missing: " + ", ".join(missing_columns)
        )

    key_label = ", ".join(columns)
    if df[columns].isna().any(axis=None):
        raise ValueError(f"Primary key ({key_label}) contains null values.")
    if df.duplicated(subset=columns).any():
        raise ValueError(f"Primary key ({key_label}) contains duplicates.")
