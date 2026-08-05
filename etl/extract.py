"""Placeholder functions for extracting raw CSV data."""

from pathlib import Path

import pandas as pd


def read_csv_file(file_path: Path) -> pd.DataFrame:
    """Return a DataFrame placeholder for a future CSV read operation."""
    # TODO: Read the CSV with the approved schema and parsing options.
    return pd.DataFrame()


def extract_table(table_name: str, file_path: Path) -> pd.DataFrame:
    """Return a placeholder DataFrame for one named source table."""
    # TODO: Validate the table name and call read_csv_file(file_path).
    return pd.DataFrame()

