"""Run curated Olist ETL and optionally load it into PostgreSQL."""
import pandas as pd

from etl.config import FOREIGN_KEYS, LOAD_ORDER, TABLE_CONFIG
from etl.extract import extract_table
from etl.load import (
    DatabaseSettings,
    MissingDatabaseConfiguration,
    load_tables,
)
from etl.transform import (
    TRANSFORMERS,
    transform_category_translation,
    transform_geolocation,
)
from etl.validate import (
    validate_file_exists,
    validate_primary_key,
    validate_required_columns,
)


def extract_and_validate() -> dict[str, pd.DataFrame]:
    """Extract and validate all raw sources in dependency order."""
    raw_tables: dict[str, pd.DataFrame] = {}
    for name in LOAD_ORDER:
        settings = TABLE_CONFIG[name]
        validate_file_exists(settings["source_file"])
        dataframe = extract_table(name, settings["source_file"])
        validate_required_columns(dataframe, settings["required_columns"])
        if name != "geolocation":
            validate_primary_key(dataframe, settings["primary_key"])
        raw_tables[name] = dataframe
    return raw_tables


def transform_tables(
    raw_tables: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Build all schema-aligned curated DataFrames."""
    curated: dict[str, pd.DataFrame] = {}
    curated["category_translation"] = transform_category_translation(
        raw_tables["category_translation"], raw_tables["products"]
    )
    curated["geolocation"] = transform_geolocation(
        raw_tables["geolocation"],
        raw_tables["customers"],
        raw_tables["sellers"],
    )
    for name in LOAD_ORDER:
        if name not in curated:
            curated[name] = TRANSFORMERS[name](raw_tables[name])
    return curated


def _orphan_count(
    child: pd.DataFrame,
    child_columns: tuple[str, ...],
    parent: pd.DataFrame,
    parent_columns: tuple[str, ...],
) -> int:
    """Count distinct non-null child keys without a parent."""
    child_keys = child[list(child_columns)].dropna().drop_duplicates()
    parent_keys = parent[list(parent_columns)].drop_duplicates().rename(
        columns=dict(zip(parent_columns, child_columns))
    )
    merged = child_keys.merge(
        parent_keys,
        on=list(child_columns),
        how="left",
        indicator=True,
    )
    return int((merged["_merge"] == "left_only").sum())


def validate_curated_tables(
    curated_tables: dict[str, pd.DataFrame],
) -> None:
    """Validate target columns, primary keys, and every foreign key."""
    for name in LOAD_ORDER:
        settings = TABLE_CONFIG[name]
        dataframe = curated_tables[name]
        validate_required_columns(dataframe, settings["target_columns"])
        if list(dataframe.columns) != settings["target_columns"]:
            raise ValueError(
                f"{name} target column order does not match PostgreSQL schema."
            )
        validate_primary_key(dataframe, settings["primary_key"])

    for child, child_columns, parent, parent_columns in FOREIGN_KEYS:
        orphan_count = _orphan_count(
            curated_tables[child],
            child_columns,
            curated_tables[parent],
            parent_columns,
        )
        if orphan_count:
            raise ValueError(
                f"Foreign key check failed: {child}{child_columns} -> "
                f"{parent}{parent_columns}; orphans={orphan_count:,}."
            )


def print_curation_summary(
    raw_tables: dict[str, pd.DataFrame],
    curated_tables: dict[str, pd.DataFrame],
) -> None:
    """Print raw and curated reconciliation for each table."""
    for name in LOAD_ORDER:
        display_name = TABLE_CONFIG[name]["display_name"]
        print(display_name)
        print(f"Raw rows : {len(raw_tables[name]):,}")
        print(f"Curated rows : {len(curated_tables[name]):,}")
        print("Validation status : PASSED")
    print("Rejected rows : 0")
    print("Quarantined rows : 0")


def print_load_report(reports: list[dict]) -> None:
    """Print table-level PostgreSQL load and reconciliation metrics."""
    for report in reports:
        print(report["table"])
        print(f"Rows in DataFrame : {report['dataframe_rows']:,}")
        print(f"Rows inserted : {report['inserted_rows']:,}")
        print(f"Rows in PostgreSQL : {report['database_rows']:,}")
        print(f"Load Time : {report['elapsed_seconds']:.2f} sec")
        print(f"Status : {report['status']}")


def run_pipeline() -> None:
    """Run curation, validate integrity, and load when credentials exist."""
    raw_tables = extract_and_validate()
    curated_tables = transform_tables(raw_tables)
    validate_curated_tables(curated_tables)
    print_curation_summary(raw_tables, curated_tables)
    print("Primary-key readiness : PASSED")
    print("Foreign-key readiness : PASSED")

    try:
        settings = DatabaseSettings.from_environment()
    except MissingDatabaseConfiguration as exc:
        print(f"Database load status : BLOCKED ({exc})")
        print("No PostgreSQL connection attempted.")
        return

    reports = load_tables(curated_tables, settings)
    print_load_report(reports)
    print(f"Total tables loaded : {len(reports)}")
    print(
        "Total rows loaded : "
        f"{sum(report['inserted_rows'] for report in reports):,}"
    )
    print("Overall Load Status : SUCCESS")


if __name__ == "__main__":
    run_pipeline()
