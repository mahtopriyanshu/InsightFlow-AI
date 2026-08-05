"""Configuration for the curated Olist PostgreSQL ETL pipeline."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw" / "olist"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DATABASE_DIR = PROJECT_ROOT / "database"
DB_SCHEMA = "olist_analytics"
UNKNOWN_CATEGORY = "__unknown__"

TABLE_CONFIG = {
    "category_translation": {
        "display_name": "Category Translation",
        "target_table": "product_category_translation",
        "source_file": RAW_DATA_DIR / "product_category_name_translation.csv",
        "required_columns": ["product_category_name", "product_category_name_english"],
        "target_columns": ["product_category_name", "product_category_name_english", "translation_status", "etl_loaded_at"],
        "primary_key": ["product_category_name"],
    },
    "geolocation": {
        "display_name": "Geolocation",
        "target_table": "geolocation",
        "source_file": RAW_DATA_DIR / "olist_geolocation_dataset.csv",
        "required_columns": ["geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng", "geolocation_city", "geolocation_state"],
        "target_columns": ["geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng", "geolocation_city", "geolocation_state", "observation_count", "coordinate_count", "geolocation_quality_status", "etl_loaded_at"],
        "primary_key": ["geolocation_zip_code_prefix"],
    },
    "customers": {
        "display_name": "Customers",
        "target_table": "customers",
        "source_file": RAW_DATA_DIR / "olist_customers_dataset.csv",
        "required_columns": ["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"],
        "target_columns": ["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state", "etl_loaded_at"],
        "primary_key": ["customer_id"],
    },
    "products": {
        "display_name": "Products",
        "target_table": "products",
        "source_file": RAW_DATA_DIR / "olist_products_dataset.csv",
        "required_columns": ["product_id", "product_category_name", "product_name_lenght", "product_description_lenght", "product_photos_qty", "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"],
        "target_columns": ["product_id", "product_category_name", "product_name_length", "product_description_length", "product_photos_qty", "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm", "etl_loaded_at"],
        "primary_key": ["product_id"],
    },
    "sellers": {
        "display_name": "Sellers",
        "target_table": "sellers",
        "source_file": RAW_DATA_DIR / "olist_sellers_dataset.csv",
        "required_columns": ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
        "target_columns": ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state", "etl_loaded_at"],
        "primary_key": ["seller_id"],
    },
    "orders": {
        "display_name": "Orders",
        "target_table": "orders",
        "source_file": RAW_DATA_DIR / "olist_orders_dataset.csv",
        "required_columns": ["order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"],
        "target_columns": ["order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date", "etl_loaded_at"],
        "primary_key": ["order_id"],
    },
    "order_items": {
        "display_name": "Order Items",
        "target_table": "order_items",
        "source_file": RAW_DATA_DIR / "olist_order_items_dataset.csv",
        "required_columns": ["order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date", "price", "freight_value"],
        "target_columns": ["order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date", "price", "freight_value", "etl_loaded_at"],
        "primary_key": ["order_id", "order_item_id"],
    },
    "payments": {
        "display_name": "Payments",
        "target_table": "order_payments",
        "source_file": RAW_DATA_DIR / "olist_order_payments_dataset.csv",
        "required_columns": ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"],
        "target_columns": ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value", "etl_loaded_at"],
        "primary_key": ["order_id", "payment_sequential"],
    },
    "reviews": {
        "display_name": "Reviews",
        "target_table": "order_reviews",
        "source_file": RAW_DATA_DIR / "olist_order_reviews_dataset.csv",
        "required_columns": ["review_id", "order_id", "review_score", "review_comment_title", "review_comment_message", "review_creation_date", "review_answer_timestamp"],
        "target_columns": ["review_id", "order_id", "review_score", "review_comment_title", "review_comment_message", "review_creation_date", "review_answer_timestamp", "etl_loaded_at"],
        "primary_key": ["review_id", "order_id"],
    },
}

LOAD_ORDER = tuple(TABLE_CONFIG)
SOURCE_FILES = {name: settings["source_file"] for name, settings in TABLE_CONFIG.items()}
CUSTOMERS_SOURCE_FILE = SOURCE_FILES["customers"]
CUSTOMERS_REQUIRED_COLUMNS = TABLE_CONFIG["customers"]["required_columns"]
CUSTOMERS_PRIMARY_KEY = "customer_id"

FOREIGN_KEYS = (
    ("customers", ("customer_zip_code_prefix",), "geolocation", ("geolocation_zip_code_prefix",)),
    ("products", ("product_category_name",), "category_translation", ("product_category_name",)),
    ("sellers", ("seller_zip_code_prefix",), "geolocation", ("geolocation_zip_code_prefix",)),
    ("orders", ("customer_id",), "customers", ("customer_id",)),
    ("order_items", ("order_id",), "orders", ("order_id",)),
    ("order_items", ("product_id",), "products", ("product_id",)),
    ("order_items", ("seller_id",), "sellers", ("seller_id",)),
    ("payments", ("order_id",), "orders", ("order_id",)),
    ("reviews", ("order_id",), "orders", ("order_id",)),
)
