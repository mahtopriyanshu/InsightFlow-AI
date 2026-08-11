"""Read-only live PostgreSQL inventory for Milestone 10."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit_app.database.connection import query_dataframe


QUERIES = {
    "schemas": "SELECT schema_name FROM information_schema.schemata ORDER BY schema_name",
    "relations": """
        SELECT n.nspname AS schema, c.relname, c.relkind,
            pg_size_pretty(pg_total_relation_size(c.oid)) AS total_size,
            COALESCE(c.reltuples::bigint, 0) AS approx_rows
        FROM pg_class AS c
        JOIN pg_namespace AS n ON n.oid = c.relnamespace
        WHERE n.nspname = 'olist_analytics'
          AND c.relkind IN ('r', 'v', 'm')
        ORDER BY c.relkind, c.relname
    """,
    "indexes": """
        SELECT tablename, indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'olist_analytics'
        ORDER BY tablename, indexname
    """,
    "constraints": """
        SELECT tc.table_name, tc.constraint_type, tc.constraint_name,
            kcu.column_name, ccu.table_name AS foreign_table,
            ccu.column_name AS foreign_column
        FROM information_schema.table_constraints AS tc
        LEFT JOIN information_schema.key_column_usage AS kcu
          ON kcu.constraint_schema = tc.constraint_schema
         AND kcu.constraint_name = tc.constraint_name
        LEFT JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_schema = tc.constraint_schema
         AND ccu.constraint_name = tc.constraint_name
        WHERE tc.table_schema = 'olist_analytics'
          AND tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY')
        ORDER BY tc.table_name, tc.constraint_type,
                 tc.constraint_name, kcu.ordinal_position
    """,
    "expected_objects": """
        SELECT name,
            to_regclass('olist_analytics.' || name)::text AS live_object
        FROM unnest(ARRAY[
            'vw_order_revenue', 'vw_order_delivery_metrics',
            'vw_customer_summary', 'vw_seller_summary',
            'vw_product_category_summary'
        ]) AS expected(name)
    """,
}


def main() -> None:
    for name, sql in QUERIES.items():
        print(f"--- {name} ---")
        print(query_dataframe(sql).to_string(index=False))


if __name__ == "__main__":
    main()
