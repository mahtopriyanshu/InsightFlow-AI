"""Show the intended ETL flow without executing real ETL work."""


def run_pipeline() -> None:
    """Display the planned Extract → Validate → Transform → Load flow."""
    print("InsightFlow AI ETL foundation")
    print("Planned flow: Extract -> Validate -> Transform -> Load")

    # TODO: Extract source CSVs into DataFrames.
    # TODO: Validate files, schemas, and primary keys.
    # TODO: Apply approved transformations.
    # TODO: Load validated DataFrames into PostgreSQL.
    print("No ETL operations are implemented in this milestone.")


if __name__ == "__main__":
    run_pipeline()
