"""Cached, read-only PostgreSQL query execution."""
import logging
from threading import RLock
from typing import Any

import pandas as pd
import psycopg
import streamlit as st

from streamlit_app.database.settings import DatabaseSettings

_QUERY_LOCK = RLock()
LOGGER = logging.getLogger(__name__)


@st.cache_resource(show_spinner=False)
def get_connection() -> psycopg.Connection:
    """Create one reusable PostgreSQL connection for the app process."""
    settings = DatabaseSettings.from_environment()
    connection = psycopg.connect(
        **settings.connection_kwargs(),
        autocommit=True,
    )
    connection.execute(
        "SET default_transaction_read_only = on; "
        "SET statement_timeout = '30s';"
    )
    return connection


def _active_connection() -> psycopg.Connection:
    """Return a live connection, recreating a closed resource if needed."""
    connection = get_connection()
    if connection.closed:
        get_connection.clear()
        connection = get_connection()
    return connection


@st.cache_data(ttl=300, show_spinner=False)
def query_dataframe(
    sql: str,
    params: tuple[Any, ...] = (),
) -> pd.DataFrame:
    """Execute a parameterized SELECT and return a DataFrame."""
    with _QUERY_LOCK:
        connection = _active_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                columns = [column.name for column in cursor.description]
        except (psycopg.InterfaceError, psycopg.OperationalError):
            LOGGER.warning("PostgreSQL connection was unavailable; recreating the cached connection")
            get_connection.clear()
            connection = _active_connection()
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                columns = [column.name for column in cursor.description]
    return pd.DataFrame(rows, columns=columns)


def healthcheck() -> tuple[bool, str]:
    """Check connectivity without exposing connection details."""
    try:
        result = query_dataframe(
            "SELECT current_database() AS database_name, "
            "current_schema() AS schema_name"
        )
        return True, str(result.iloc[0]["database_name"])
    except Exception as exc:
        LOGGER.error("PostgreSQL health check failed (%s)", type(exc).__name__)
        return False, "database connection unavailable"
