"""Structural SQL governance using sqlglot plus explicit policy checks."""
import re
import sqlglot
from sqlglot import exp

from streamlit_app.assistant.models import SQLValidationError
from streamlit_app.assistant.semantic import ALLOWED_COLUMNS, ALLOWED_TABLES

BANNED_WORDS = {"insert", "update", "delete", "drop", "alter", "truncate", "create", "grant", "revoke", "copy", "call", "do", "merge", "refresh", "vacuum", "analyze", "reindex", "cluster"}
BANNED_FUNCTIONS = {"pg_read_file", "pg_read_binary_file", "pg_ls_dir", "pg_stat_file", "lo_import", "lo_export", "dblink", "current_setting", "set_config"}
MAX_JOINS = 14
MAX_LIMIT = 100


def validate_sql(sql: str) -> None:
    if "--" in sql or "/*" in sql or "*/" in sql:
        raise SQLValidationError("SQL comments are not allowed.")
    lowered = sql.lower()
    if re.search(r"\b(information_schema|pg_catalog)\b", lowered):
        raise SQLValidationError("System catalogs are not available to assistant queries.")
    if any(re.search(rf"\b{word}\b", lowered) for word in BANNED_WORDS):
        raise SQLValidationError("Only read-only SELECT analytics are allowed.")
    parseable = re.sub(r"%s", "0", sql)
    try:
        statements = sqlglot.parse(parseable, read="postgres")
    except sqlglot.errors.ParseError as exc:
        raise SQLValidationError("Generated SQL could not be parsed safely.") from exc
    if len(statements) != 1:
        raise SQLValidationError("Multiple SQL statements are not allowed.")
    tree = statements[0]
    if not isinstance(tree, exp.Select):
        raise SQLValidationError("The query must resolve to a SELECT statement.")
    if any(isinstance(node, (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Command)) for node in tree.walk()):
        raise SQLValidationError("A non-read-only SQL node was rejected.")
    ctes = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        name = table.name.lower(); schema = table.db.lower() if table.db else ""
        if name not in ALLOWED_TABLES and name not in ctes:
            raise SQLValidationError(f"Table '{name}' is outside the semantic allowlist.")
        if schema and schema != "olist_analytics":
            raise SQLValidationError("Only the olist_analytics schema is allowed.")
    for column in tree.find_all(exp.Column):
        if column.name.lower() not in ALLOWED_COLUMNS:
            raise SQLValidationError(f"Column '{column.name}' is outside the semantic allowlist.")
    for select in tree.find_all(exp.Select):
        if any(isinstance(item, exp.Star) for item in select.expressions):
            raise SQLValidationError("SELECT * is not allowed.")
    joins = list(tree.find_all(exp.Join))
    if len(joins) > MAX_JOINS:
        raise SQLValidationError("Query join complexity exceeds the governed limit.")
    for join in joins:
        if str(join.args.get("kind") or "").upper() == "CROSS":
            raise SQLValidationError("Cartesian joins are not allowed.")
    for function in tree.find_all(exp.Func):
        function_name = (getattr(function, "name", "") or function.sql_name()).lower()
        if function_name in BANNED_FUNCTIONS:
            raise SQLValidationError("Unsafe database functions are not allowed.")
    for limit in tree.find_all(exp.Limit):
        expression = limit.expression
        if isinstance(expression, exp.Literal) and expression.is_int and int(expression.this) > MAX_LIMIT:
            raise SQLValidationError(f"LIMIT cannot exceed {MAX_LIMIT} rows.")
