"""Configuration for the complete Olist ETL pipeline."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw" / "olist"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DATABASE_DIR = PROJECT_ROOT / "database"

TABLE_CONFIG = {
    "category_translation": {
        "display_name": "Category Translation",
        "source_file": RAW_DATA_DIR / "product_category_name_translation.csv",
        "required_columns": [
            "product_category_name",
            "product_category_name_english",
        ],
        "primary_key": ["product_category_name"],
    },
    "geolocation": {
        "display_name": "Geolocation",
        "source_file": RAW_DATA_DIR / "olist_geolocation_dataset.csv",
        "required_columns": [
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
            "geolocation_city",
            "geolocation_state",
        ],
        "primary_key": None,
    },
    "customers": {
        "display_name": "Customers",
        "source_file": RAW_DATA_DIR / "olist_customers_dataset.csv",
        "required_columns": [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
        "primary_key": ["customer_id"],
    },
    "products": {
        "display_name": "Products",
        "source_file": RAW_DATA_DIR / "olist_products_dataset.csv",
        "required_columns": [
            "product_id",
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
        "primary_key": ["product_id"],
    },
    "sellers": {
        "display_name": "Sellers",
        "source_file": RAW_DATA_DIR / "olist_sellers_dataset.csv",
        "required_columns": [
            "seller_id",
            "seller_zip_code_prefix",
            "seller_city",
            "seller_state",
        ],
        "primary_key": ["seller_id"],
    },
    "orders": {
        "display_name": "Orders",
        "source_file": RAW_DATA_DIR / "olist_orders_dataset.csv",
        "required_columns": [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
        "primary_key": ["order_id"],
    },
    "order_items": {
        "display_name": "Order Items",
        "source_file": RAW_DATA_DIR / "olist_order_items_dataset.csv",
        "required_columns": [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
        "primary_key": ["order_id", "order_item_id"],
    },
    "payments": {
        "display_name": "Payments",
        "source_file": RAW_DATA_DIR / "olist_order_payments_dataset.csv",
        "required_columns": [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ],
        "primary_key": ["order_id", "payment_sequential"],
    },
    "reviews": {
        "display_name": "Reviews",
        "source_file": RAW_DATA_DIR / "olist_order_reviews_dataset.csv",
        "required_columns": [
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ],
        "primary_key": ["review_id", "order_id"],
    },
}

SOURCE_FILES = {
    table_name: settings["source_file"]
    for table_name, settings in TABLE_CONFIG.items()
}

CUSTOMERS_SOURCE_FILE = SOURCE_FILES["customers"]
CUSTOMERS_REQUIRED_COLUMNS = TABLE_CONFIG["customers"]["required_columns"]
CUSTOMERS_PRIMARY_KEY = "customer_id"
