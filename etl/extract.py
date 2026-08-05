"""Extraction helpers for raw CSV sources."""
from pathlib import Path
import pandas as pd


def read_csv_file(path: Path) -> pd.DataFrame:
    """Read a CSV source into a DataFrame or raise a clear error."""
    source_path = Path(path)
    try:
        return pd.read_csv(source_path)
    except (OSError, pd.errors.ParserError, UnicodeError) as exc:
        raise ValueError(f"Unable to read source CSV '{source_path}': {exc}") from exc


def extract_table(table_name: str, path: Path) -> pd.DataFrame:
    """Extract the configured customers table."""
    if table_name != "customers":
        raise ValueError(
            f"Unsupported table '{table_name}'; only 'customers' is configured."
        )
    return read_csv_file(path)
