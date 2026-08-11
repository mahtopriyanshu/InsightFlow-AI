"""Dedicated bounded read-only PostgreSQL executor for assistant queries."""
from time import perf_counter
import pandas as pd
import psycopg

from streamlit_app.assistant.models import AssistantError, QueryTimeoutError, SafeExecutionError
from streamlit_app.database.settings import DatabaseSettings

MAX_RESULT_ROWS = 100
STATEMENT_TIMEOUT_MS = 10_000


def execute_read_only(sql: str, params: tuple[object, ...]) -> tuple[pd.DataFrame, float]:
    settings = DatabaseSettings.from_environment(); kwargs = settings.connection_kwargs()
    kwargs["application_name"] = "insightflow_governed_assistant"
    kwargs["options"] = f"-c default_transaction_read_only=on -c statement_timeout={STATEMENT_TIMEOUT_MS}"
    started = perf_counter()
    try:
        with psycopg.connect(**kwargs, autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchmany(MAX_RESULT_ROWS + 1)
                if len(rows) > MAX_RESULT_ROWS:
                    raise AssistantError(f"The governed result limit is {MAX_RESULT_ROWS} rows.")
                columns = [column.name for column in cursor.description]
    except psycopg.errors.QueryCanceled:
        raise QueryTimeoutError("The governed query exceeded the safe execution timeout.")
    except psycopg.Error:
        raise SafeExecutionError("The verified database query could not be completed safely.")
    return pd.DataFrame(rows, columns=columns), (perf_counter() - started) * 1000
