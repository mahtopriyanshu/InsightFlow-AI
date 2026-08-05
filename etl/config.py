"""Central configuration for the future ETL pipeline."""

from pathlib import Path


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw" / "olist"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DATABASE_DIR = PROJECT_ROOT / "database"

# Source files
SOURCE_FILES = {
    "customers": RAW_DATA_DIR / "olist_customers_dataset.csv",
    "geolocation": RAW_DATA_DIR / "olist_geolocation_dataset.csv",
    "order_items": RAW_DATA_DIR / "olist_order_items_dataset.csv",
    "order_payments": RAW_DATA_DIR / "olist_order_payments_dataset.csv",
    "order_reviews": RAW_DATA_DIR / "olist_order_reviews_dataset.csv",
    "orders": RAW_DATA_DIR / "olist_orders_dataset.csv",
    "products": RAW_DATA_DIR / "olist_products_dataset.csv",
    "sellers": RAW_DATA_DIR / "olist_sellers_dataset.csv",
    "category_translation": RAW_DATA_DIR / "product_category_name_translation.csv",
}

# PostgreSQL placeholders
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_DATABASE = "insightflow_ai"
POSTGRES_USER = "your_username"
POSTGRES_PASSWORD = "your_password"
POSTGRES_SCHEMA = "olist_analytics"

