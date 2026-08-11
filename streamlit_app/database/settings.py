"""Environment-backed application settings."""
from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)


@dataclass(frozen=True)
class DatabaseSettings:
    """Validated PostgreSQL connection settings."""

    host: str
    port: int
    dbname: str
    user: str
    password: str

    @classmethod
    def from_environment(cls) -> "DatabaseSettings":
        names = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
        missing = [name for name in names if not os.getenv(name)]
        if missing:
            raise ValueError(
                "Missing database configuration: " + ", ".join(missing)
            )
        return cls(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
        )

    def connection_kwargs(self) -> dict[str, object]:
        """Return psycopg-compatible connection arguments."""
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password,
            "connect_timeout": 8,
            "application_name": "insightflow_streamlit",
        }
