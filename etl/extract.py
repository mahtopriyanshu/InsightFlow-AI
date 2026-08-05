"""Extraction helpers for configured Olist CSV sources."""
from pathlib import Path

import pandas as pd

from etl.config import SOURCE_FILES


def read_csv_file(path: Path) -> pd.DataFrame:
    """Read a CSV source into a DataFrame or raise a clear error."""
    source_path = Path(path)
    try:
        return pd.read_csv(source_path)
    except (OSError, pd.errors.ParserError, UnicodeError) as exc:
        raise ValueError(f"Unable to read source CSV '{source_path}': {exc}") from exc


def extract_table(table_name: str, path: Path | None = None) -> pd.DataFrame:
    """Extract one configured Olist table from its CSV source."""
    if table_name not in SOURCE_FILES:
        supported = ", ".join(SOURCE_FILES)
        raise ValueError(
            f"Unsupported table '{table_name}'. Configured tables: {supported}."
        )
    source_path = SOURCE_FILES[table_name] if path is None else Path(path)
    return read_csv_file(source_path)
