"""Row-preserving transformations for Olist data."""
from collections.abc import Callable

import pandas as pd


def _transform_table(df: pd.DataFrame) -> pd.DataFrame:
    """Copy data, trim text boundaries, and add one UTC batch timestamp."""
    transformed = df.copy(deep=True)
    text_columns = transformed.select_dtypes(include=["object", "string"]).columns
    for column in text_columns:
        transformed[column] = transformed[column].str.strip()
    transformed["etl_loaded_at"] = pd.Timestamp.now(tz="UTC")
    return transformed


def transform_category_translation(df: pd.DataFrame) -> pd.DataFrame:
    return _transform_table(df)


def transform_geolocation(df: pd.DataFrame) -> pd.DataFrame:
    return _transform_table(df)


def transform_customers(df: pd.DataFrame) -> pd.DataFrame:
    return _transform_table(df)


def transform_products(df: pd.DataFrame) -> pd.DataFrame:
    return _transform_table(df)


def transform_sellers(df: pd.DataFrame) -> pd.DataFrame:
    return _transform_table(df)


def transform_orders(df: pd.DataFrame) -> pd.DataFrame:
    return _transform_table(df)


def transform_order_items(df: pd.DataFrame) -> pd.DataFrame:
    return _transform_table(df)


def transform_payments(df: pd.DataFrame) -> pd.DataFrame:
    return _transform_table(df)


def transform_reviews(df: pd.DataFrame) -> pd.DataFrame:
    return _transform_table(df)


TRANSFORMERS: dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {
    "category_translation": transform_category_translation,
    "geolocation": transform_geolocation,
    "customers": transform_customers,
    "products": transform_products,
    "sellers": transform_sellers,
    "orders": transform_orders,
    "order_items": transform_order_items,
    "payments": transform_payments,
    "reviews": transform_reviews,
}
