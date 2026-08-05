"""Configuration for the Customers ETL pipeline."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw" / "olist"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DATABASE_DIR = PROJECT_ROOT / "database"
CUSTOMERS_SOURCE_FILE = RAW_DATA_DIR / "olist_customers_dataset.csv"
SOURCE_FILES = {"customers": CUSTOMERS_SOURCE_FILE}
CUSTOMERS_REQUIRED_COLUMNS = [
    "customer_id", "customer_unique_id", "customer_zip_code_prefix",
    "customer_city", "customer_state",
]
CUSTOMERS_PRIMARY_KEY = "customer_id"
