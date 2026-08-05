"""Run the Customers-only Extract -> Validate -> Transform pipeline."""
from etl.config import (
    CUSTOMERS_PRIMARY_KEY, CUSTOMERS_REQUIRED_COLUMNS, CUSTOMERS_SOURCE_FILE,
)
from etl.extract import extract_table
from etl.transform import transform_customers
from etl.validate import (
    validate_file_exists, validate_primary_key, validate_required_columns,
)


def run_pipeline() -> None:
    """Extract, validate, and transform the official customers source."""
    validate_file_exists(CUSTOMERS_SOURCE_FILE)
    customers = extract_table("customers", CUSTOMERS_SOURCE_FILE)
    print(f"Rows read: {len(customers):,}")
    validate_required_columns(customers, CUSTOMERS_REQUIRED_COLUMNS)
    validate_primary_key(customers, CUSTOMERS_PRIMARY_KEY)
    print("Validation passed")
    transformed_customers = transform_customers(customers)
    print(f"Rows transformed: {len(transformed_customers):,}")
    print(f"Output columns: {list(transformed_customers.columns)}")


if __name__ == "__main__":
    run_pipeline()
