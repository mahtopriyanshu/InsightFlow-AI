"""Transformations for customer data."""
import pandas as pd


def transform_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Copy customer data, trim text boundaries, and add batch load time."""
    transformed = df.copy(deep=True)
    text_columns = transformed.select_dtypes(include=["object", "string"]).columns
    for column in text_columns:
        transformed[column] = transformed[column].str.strip()
    batch_loaded_at = pd.Timestamp.now(tz="UTC")
    transformed["etl_loaded_at"] = batch_loaded_at
    return transformed
