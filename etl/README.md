# ETL Foundation

## Purpose

This folder contains the lightweight foundation for the future InsightFlow AI ETL pipeline. Milestone 4C Part A defines module responsibilities and the intended flow only. It does not read source data, transform records, connect to PostgreSQL, or load tables.

## Modules

### `config.py`

Keeps project paths, source-file locations, and PostgreSQL placeholders in one place. Future milestones should replace credential placeholders with environment-variable values rather than committing real passwords.

### `extract.py`

Defines typed placeholders for reading one CSV file and extracting one named table. Future work will implement pandas CSV reading with approved schema and timestamp options.

### `validate.py`

Defines simple placeholders for checking file existence, required columns, and primary-key validity. Future work will replace placeholder results with real checks and readable validation messages.

### `transform.py`

Defines placeholders for general cleaning and table-specific transformations. The functions currently return DataFrames unchanged because no transformation logic is approved for this milestone.

### `load.py`

Defines placeholders for loading DataFrames and named tables into PostgreSQL. The functions do not create a connection and currently report that no load occurred.

### `run_pipeline.py`

Shows the intended pipeline order without running ETL operations:

```text
Extract → Validate → Transform → Load
```

### `__init__.py`

Marks `etl` as a Python package so its modules can be imported consistently.

## Expected Execution Flow

1. Read all configuration from `config.py`.
2. Extract one approved source CSV into a pandas DataFrame.
3. Validate the file, required columns, and primary key.
4. Apply approved table-specific transformations.
5. Load the validated DataFrame into the correct PostgreSQL table.
6. Repeat in the dependency order documented in `docs/05_etl_design.md`.

## Future Expansion

Recommended implementation sequence:

1. Implement real file and schema validation.
2. Implement CSV extraction for one small table.
3. Add primary-key and required-column checks.
4. Add approved datatype and timestamp conversions.
5. Add category and geolocation transformations.
6. Add PostgreSQL connection configuration through environment variables.
7. Implement table loading in dependency order.
8. Add simple reconciliation tests for rows, keys, and foreign keys.

The project should remain analytics-focused. Advanced orchestration, retry frameworks, APIs, cloud services, Docker, and scheduling are outside this foundation.

