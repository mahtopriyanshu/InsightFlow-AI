"""Placeholder functions for future cleaning and transformation."""

import pandas as pd


def clean_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return the input unchanged until cleaning rules are approved."""
    # TODO: Apply approved null, duplicate, and datatype rules.
    return dataframe


def transform_table(
    table_name: str,
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Return the input unchanged until table-specific rules are added."""
    # TODO: Route to the approved transformation for table_name.
    return dataframe

