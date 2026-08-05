"""Run the complete Olist Extract -> Validate -> Transform pipeline."""
from etl.config import TABLE_CONFIG
from etl.extract import extract_table
from etl.transform import TRANSFORMERS
from etl.validate import (
    validate_file_exists,
    validate_primary_key,
    validate_required_columns,
)


def process_table(table_name: str, settings: dict) -> int:
    """Extract, validate, and transform one configured Olist table."""
    display_name = settings["display_name"]
    source_file = settings["source_file"]

    validate_file_exists(source_file)
    source = extract_table(table_name, source_file)
    print(f"{display_name} - Rows read: {len(source):,}")

    validate_required_columns(source, settings["required_columns"])
    primary_key = settings["primary_key"]
    if primary_key is not None:
        validate_primary_key(source, primary_key)
    print(f"{display_name} - Validation passed")

    transformed = TRANSFORMERS[table_name](source)
    print(f"{display_name} - Rows transformed: {len(transformed):,}")
    return len(transformed)


def run_pipeline() -> None:
    """Process all configured Olist tables in dependency order."""
    total_rows = 0
    for table_name, settings in TABLE_CONFIG.items():
        total_rows += process_table(table_name, settings)

    print(f"Total tables processed: {len(TABLE_CONFIG)}")
    print(f"Total rows processed: {total_rows:,}")
    print("Overall ETL status: SUCCESS")


if __name__ == "__main__":
    run_pipeline()
