"""Apply the non-destructive Milestone 10 analytics-serving migration."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import psycopg

from streamlit_app.database.settings import DatabaseSettings


def main() -> None:
    settings = DatabaseSettings.from_environment()
    sql = (PROJECT_ROOT / "database" / "milestone10_analytics_serving.sql").read_text()
    with psycopg.connect(**settings.connection_kwargs()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)
        connection.commit()
    print("Milestone 10 analytics-serving migration applied.")


if __name__ == "__main__":
    main()
