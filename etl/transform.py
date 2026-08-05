"""Curated, schema-aligned transformations for Olist data."""
from collections.abc import Callable

import numpy as np
import pandas as pd

from etl.config import UNKNOWN_CATEGORY


def _batch_timestamp() -> pd.Timestamp:
    """Return one timezone-aware UTC timestamp for a transformed table."""
    return pd.Timestamp.now(tz="UTC")


def _trim_text(df: pd.DataFrame) -> pd.DataFrame:
    """Return a deep copy with boundary whitespace removed from text fields."""
    transformed = df.copy(deep=True)
    text_columns = transformed.select_dtypes(include=["object", "string"]).columns
    for column in text_columns:
        transformed[column] = transformed[column].str.strip()
    return transformed


def _transform_table(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the shared row-preserving curated transformation."""
    transformed = _trim_text(df)
    transformed["etl_loaded_at"] = _batch_timestamp()
    return transformed


def _canonical_labels(
    observations: pd.DataFrame,
    zip_column: str,
    city_column: str,
    state_column: str,
) -> pd.DataFrame:
    """Choose the most frequent city/state pair, breaking ties lexically."""
    frequencies = (
        observations.groupby(
            [zip_column, city_column, state_column],
            dropna=False,
        )
        .size()
        .rename("label_support_count")
        .reset_index()
        .sort_values(
            [zip_column, "label_support_count", state_column, city_column],
            ascending=[True, False, True, True],
            kind="mergesort",
        )
    )
    return frequencies.drop_duplicates(zip_column, keep="first")


def transform_category_translation(
    df: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    """Add missing translations and a controlled Unknown category member."""
    supplied = _trim_text(df)
    supplied["translation_status"] = "translated"
    product_categories = (
        products["product_category_name"].dropna().astype("string").str.strip()
    )
    translated = set(supplied["product_category_name"])
    missing = sorted(set(product_categories) - translated)
    generated = pd.DataFrame(
        {
            "product_category_name": [*missing, UNKNOWN_CATEGORY],
            "product_category_name_english": [None] * (len(missing) + 1),
            "translation_status": (
                ["missing_translation"] * len(missing) + ["unknown"]
            ),
        }
    )
    curated = pd.concat([supplied, generated], ignore_index=True)
    curated["etl_loaded_at"] = _batch_timestamp()
    return curated


def transform_geolocation(
    df: pd.DataFrame,
    customers: pd.DataFrame,
    sellers: pd.DataFrame,
) -> pd.DataFrame:
    """Consolidate geography deterministically and add unmatched ZIP members.

    Latitude and longitude are independent medians rounded to seven decimals.
    City/state is the most frequent pair across raw rows, with ties resolved
    by ascending state then city. Observation count includes every raw row;
    coordinate count counts distinct coordinate pairs. Multiple city/state
    pairs mark a ZIP ambiguous. Missing entity ZIPs use source-derived labels,
    null coordinates, zero counts, and unmatched quality.
    """
    raw = _trim_text(df)
    required = [
        "geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng",
        "geolocation_city", "geolocation_state",
    ]
    if raw[required].isna().any(axis=None):
        raise ValueError("Geolocation contains null required values.")
    if not raw["geolocation_lat"].between(-90, 90).all():
        raise ValueError("Geolocation contains latitude outside [-90, 90].")
    if not raw["geolocation_lng"].between(-180, 180).all():
        raise ValueError("Geolocation contains longitude outside [-180, 180].")
    if not raw["geolocation_state"].str.fullmatch(r"[A-Z]{2}").all():
        raise ValueError("Geolocation contains invalid state codes.")

    zip_column = "geolocation_zip_code_prefix"
    aggregates = (
        raw.groupby(zip_column, sort=True)
        .agg(
            geolocation_lat=("geolocation_lat", "median"),
            geolocation_lng=("geolocation_lng", "median"),
            observation_count=(zip_column, "size"),
        )
        .reset_index()
    )
    coordinate_counts = (
        raw.drop_duplicates([zip_column, "geolocation_lat", "geolocation_lng"])
        .groupby(zip_column)
        .size()
        .rename("coordinate_count")
        .reset_index()
    )
    labels = _canonical_labels(
        raw, zip_column, "geolocation_city", "geolocation_state"
    )
    label_counts = (
        raw.drop_duplicates(
            [zip_column, "geolocation_city", "geolocation_state"]
        )
        .groupby(zip_column)
        .size()
        .rename("label_count")
        .reset_index()
    )
    curated = (
        aggregates.merge(coordinate_counts, on=zip_column, validate="one_to_one")
        .merge(
            labels[[zip_column, "geolocation_city", "geolocation_state"]],
            on=zip_column,
            validate="one_to_one",
        )
        .merge(label_counts, on=zip_column, validate="one_to_one")
    )
    curated["geolocation_lat"] = curated["geolocation_lat"].round(7)
    curated["geolocation_lng"] = curated["geolocation_lng"].round(7)
    curated["geolocation_quality_status"] = np.where(
        curated.pop("label_count").eq(1), "matched", "ambiguous"
    )

    entity_locations = pd.concat(
        [
            customers[
                ["customer_zip_code_prefix", "customer_city", "customer_state"]
            ].rename(
                columns={
                    "customer_zip_code_prefix": zip_column,
                    "customer_city": "geolocation_city",
                    "customer_state": "geolocation_state",
                }
            ),
            sellers[
                ["seller_zip_code_prefix", "seller_city", "seller_state"]
            ].rename(
                columns={
                    "seller_zip_code_prefix": zip_column,
                    "seller_city": "geolocation_city",
                    "seller_state": "geolocation_state",
                }
            ),
        ],
        ignore_index=True,
    )
    entity_locations = _trim_text(entity_locations)
    missing_locations = entity_locations[
        ~entity_locations[zip_column].isin(curated[zip_column])
    ]
    missing_labels = _canonical_labels(
        missing_locations, zip_column, "geolocation_city", "geolocation_state"
    )
    controlled = missing_labels[
        [zip_column, "geolocation_city", "geolocation_state"]
    ].copy()
    controlled["geolocation_lat"] = None
    controlled["geolocation_lng"] = None
    controlled["observation_count"] = 0
    controlled["coordinate_count"] = 0
    controlled["geolocation_quality_status"] = "unmatched"

    curated = pd.concat([curated, controlled], ignore_index=True)
    curated = curated[
        [
            zip_column, "geolocation_lat", "geolocation_lng",
            "geolocation_city", "geolocation_state", "observation_count",
            "coordinate_count", "geolocation_quality_status",
        ]
    ].sort_values(zip_column, kind="mergesort", ignore_index=True)
    curated["etl_loaded_at"] = _batch_timestamp()
    return curated


def transform_customers(df: pd.DataFrame) -> pd.DataFrame:
    return _transform_table(df)


def transform_products(df: pd.DataFrame) -> pd.DataFrame:
    """Align source headers and map null category keys to Unknown."""
    transformed = _trim_text(df).rename(
        columns={
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
        }
    )
    transformed["product_category_name"] = transformed[
        "product_category_name"
    ].fillna(UNKNOWN_CATEGORY)
    integer_columns = [
        "product_name_length",
        "product_description_length",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]
    transformed[integer_columns] = transformed[integer_columns].astype("Int64")
    transformed["etl_loaded_at"] = _batch_timestamp()
    return transformed


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
    "customers": transform_customers,
    "products": transform_products,
    "sellers": transform_sellers,
    "orders": transform_orders,
    "order_items": transform_order_items,
    "payments": transform_payments,
    "reviews": transform_reviews,
}
