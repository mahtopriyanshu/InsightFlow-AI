"""Functional data, search, report, and safety regression checks."""
from pathlib import Path
import sys
from time import perf_counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit_app.database.connection import healthcheck, query_dataframe
from streamlit_app.pages.reports import _excel_bytes
from streamlit_app.services import commerce, customers
from streamlit_app.services.common import get_filter_options
from streamlit_app.services.reports import get_report_dataset
from streamlit_app.utils.filters import FilterState


def main() -> None:
    start, end, _, _ = get_filter_options()
    filters = FilterState(start, end)
    customer_id = customers.get_top_customers(filters, 1).iloc[0]["customer_unique_id"]
    category = commerce.get_product_performance(filters, 1).iloc[0]["category"]
    seller_id = commerce.get_seller_performance(filters, 1).iloc[0]["seller_id"]
    print("health", healthcheck())
    print("searches", {
        "customer": len(customers.search_customers(str(customer_id)[:8])),
        "product": len(commerce.search_products(str(category))),
        "seller": len(commerce.search_sellers(str(seller_id)[:8])),
    })
    for name in (
        "Order performance", "Customer summary",
        "Seller performance", "Category performance",
    ):
        started = perf_counter()
        data = get_report_dataset(name, filters, 50_000)
        elapsed_ms = 1000 * (perf_counter() - started)
        csv_data = data.to_csv(index=False).encode("utf-8")
        excel_data = _excel_bytes(data, name)
        print("report", name, {
            "rows": len(data), "query_ms": round(elapsed_ms, 1),
            "csv_bytes": len(csv_data), "xlsx_bytes": len(excel_data),
            "xlsx_signature": excel_data[:2].decode("ascii"),
        })
    print("counts")
    print(query_dataframe("""
        SELECT 'customers' AS table_name, COUNT(*) AS rows
          FROM olist_analytics.customers
        UNION ALL SELECT 'orders', COUNT(*) FROM olist_analytics.orders
        UNION ALL SELECT 'order_items', COUNT(*) FROM olist_analytics.order_items
        UNION ALL SELECT 'order_payments', COUNT(*) FROM olist_analytics.order_payments
        UNION ALL SELECT 'order_reviews', COUNT(*) FROM olist_analytics.order_reviews
        UNION ALL SELECT 'products', COUNT(*) FROM olist_analytics.products
        UNION ALL SELECT 'sellers', COUNT(*) FROM olist_analytics.sellers
        ORDER BY table_name
    """).to_string(index=False))
    print("objects")
    print(query_dataframe("""
        SELECT c.relname, c.relkind, COALESCE(c.reltuples::bigint, 0) AS approx_rows
        FROM pg_class AS c
        JOIN pg_namespace AS n ON n.oid = c.relnamespace
        WHERE n.nspname = 'olist_analytics'
          AND c.relname IN (
            'mv_order_revenue', 'vw_order_revenue',
            'vw_order_delivery_metrics'
          )
        ORDER BY c.relname
    """).to_string(index=False))


if __name__ == "__main__":
    main()
