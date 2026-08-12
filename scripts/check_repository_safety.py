"""Fail CI when forbidden local secrets or database exports are tracked."""
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_EXACT = {
    ".env",
    ".streamlit/secrets.toml",
    "docs/api key details.txt",
}
FORBIDDEN_SUFFIXES = {".dump", ".backup", ".bak"}
REQUIRED_PLACEHOLDERS = {
    "DB_HOST": "your_database_host",
    "DB_PORT": "your_database_port",
    "DB_NAME": "your_database_name",
    "DB_USER": "your_database_user",
    "DB_PASSWORD": "your_database_password",
    "AI_API_KEY": "your_api_key_here",
}


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def main() -> None:
    tracked = tracked_files()
    forbidden = []
    for name in tracked:
        normalized = name.replace("\\", "/").lower()
        path = Path(normalized)
        if (
            normalized in FORBIDDEN_EXACT
            or (path.name.startswith(".env") and path.name != ".env.example")
            or path.suffix in FORBIDDEN_SUFFIXES
        ):
            forbidden.append(name)
    if forbidden:
        raise SystemExit(
            "Repository safety check failed: forbidden tracked path(s): "
            + ", ".join(sorted(forbidden))
        )

    example_path = ROOT / ".env.example"
    values = {}
    for raw_line in example_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    invalid = [
        key for key, placeholder in REQUIRED_PLACEHOLDERS.items()
        if values.get(key) != placeholder
    ]
    if invalid:
        raise SystemExit(
            ".env.example safety check failed for placeholder field(s): "
            + ", ".join(invalid)
        )

    print("Repository safety checks passed; no forbidden tracked files found.")


if __name__ == "__main__":
    main()
