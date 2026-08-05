"""Placeholder functions for future PostgreSQL loading."""

import pandas as pd


def load_dataframe(dataframe: pd.DataFrame, table_name: str) -> bool:
    """Return a placeholder result for a future PostgreSQL load."""
    # TODO: Load the DataFrame after a database connection is approved.
    return False


def load_table(table_name: str, dataframe: pd.DataFrame) -> bool:
    """Return a placeholder result for loading one curated table."""
    # TODO: Validate load order and call load_dataframe().
    return False

