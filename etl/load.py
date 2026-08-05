"""Transactional PostgreSQL COPY loading for curated Olist tables."""
from dataclasses import dataclass
import os
from time import perf_counter
from typing import Any

import pandas as pd
from dotenv import load_dotenv

from etl.config import DB_SCHEMA, LOAD_ORDER, PROJECT_ROOT, TABLE_CONFIG

load_dotenv(PROJECT_ROOT / ".env", override=False)

REQUIRED_DB_VARIABLES = (
    "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD",
)


class MissingDatabaseConfiguration(ValueError):
    """Raised when required database environment variables are absent."""


@dataclass(frozen=True)
class DatabaseSettings:
    """PostgreSQL connection settings sourced only from the environment."""

    host: str
    port: int
    dbname: str
    user: str
    password: str

    @classmethod
    def from_environment(cls) -> "DatabaseSettings":
        missing = [name for name in REQUIRED_DB_VARIABLES if not os.getenv(name)]
        if missing:
            raise MissingDatabaseConfiguration(
                "Missing database environment variables: " + ", ".join(missing)
            )
        try:
            port = int(os.environ["DB_PORT"])
        except ValueError as exc:
            raise MissingDatabaseConfiguration(
                "DB_PORT must be an integer."
            ) from exc
        return cls(
            host=os.environ["DB_HOST"],
            port=port,
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
        )

    def connection_kwargs(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password,
        }


def _python_value(value: Any) -> Any:
    """Convert pandas/numpy missing and scalar values for psycopg."""
    if pd.isna(value):
        return None
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()
    if hasattr(value, "item"):
        return value.item()
    return value


def _table_count(cursor: Any, table_name: str) -> int:
    """Return a destination row count using safely quoted identifiers."""
    from psycopg import sql

    statement = sql.SQL("SELECT count(*) FROM {}.{}").format(
        sql.Identifier(DB_SCHEMA),
        sql.Identifier(table_name),
    )
    cursor.execute(statement)
    return int(cursor.fetchone()[0])


def _ensure_destinations_empty(cursor: Any) -> None:
    """Fail before loading if any destination table already contains data."""
    for name in LOAD_ORDER:
        table_name = TABLE_CONFIG[name]["target_table"]
        row_count = _table_count(cursor, table_name)
        if row_count:
            raise ValueError(
                f"Destination table '{DB_SCHEMA}.{table_name}' already "
                f"contains {row_count:,} rows."
            )


def load_dataframe(
    cursor: Any,
    dataframe: pd.DataFrame,
    table_name: str,
) -> int:
    """Bulk-load one DataFrame through PostgreSQL COPY."""
    from psycopg import sql

    columns = list(dataframe.columns)
    statement = sql.SQL("COPY {}.{} ({}) FROM STDIN").format(
        sql.Identifier(DB_SCHEMA),
        sql.Identifier(table_name),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
    )
    with cursor.copy(statement) as copy:
        for row in dataframe.itertuples(index=False, name=None):
            copy.write_row(tuple(_python_value(value) for value in row))
    return len(dataframe)


def load_tables(
    curated_tables: dict[str, pd.DataFrame],
    settings: DatabaseSettings,
) -> list[dict[str, Any]]:
    """Load all tables atomically and reconcile each before commit."""
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError(
            "psycopg 3 is required; install project requirements first."
        ) from exc

    reports: list[dict[str, Any]] = []
    failing_table = "connection/preflight"
    try:
        with psycopg.connect(**settings.connection_kwargs()) as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    _ensure_destinations_empty(cursor)
                    for name in LOAD_ORDER:
                        failing_table = TABLE_CONFIG[name]["target_table"]
                        dataframe = curated_tables[name]
                        started = perf_counter()
                        inserted = load_dataframe(
                            cursor, dataframe, failing_table
                        )
                        database_rows = _table_count(cursor, failing_table)
                        if database_rows != len(dataframe):
                            raise ValueError(
                                f"Reconciliation failed for {failing_table}: "
                                f"DataFrame={len(dataframe):,}, "
                                f"PostgreSQL={database_rows:,}."
                            )
                        reports.append(
                            {
                                "table": failing_table,
                                "dataframe_rows": len(dataframe),
                                "inserted_rows": inserted,
                                "database_rows": database_rows,
                                "elapsed_seconds": perf_counter() - started,
                                "status": "SUCCESS",
                            }
                        )
    except Exception as exc:
        print(f"Failing table: {failing_table}")
        print(f"Load error: {exc}")
        print("Transaction status: ROLLED BACK")
        raise
    return reports
