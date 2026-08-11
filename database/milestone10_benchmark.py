"""One-pass before/after benchmark for representative Streamlit workloads."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.milestone10_validate import execution_ms, optimized_cte
from streamlit_app.services.common import fallback_orders_cte, get_filter_options
from streamlit_app.utils.filters import FilterState


COMMON = {
    "sales_trend": """
        SELECT date_trunc('month',f.order_purchase_timestamp)::date,
          COUNT(*),SUM(v.payment_revenue),AVG(v.payment_revenue)
        FROM filtered_orders f LEFT JOIN order_revenue v ON v.order_id=f.order_id
        GROUP BY 1 ORDER BY 1
    """,
    "category_ranking": """
        SELECT COALESCE(t.product_category_name_english,p.product_category_name),
          COUNT(DISTINCT i.order_id),COUNT(*),SUM(i.price)
        FROM filtered_orders f
        JOIN olist_analytics.order_items i ON i.order_id=f.order_id
        JOIN olist_analytics.products p ON p.product_id=i.product_id
        LEFT JOIN olist_analytics.product_category_translation t
          ON t.product_category_name=p.product_category_name
        GROUP BY 1 ORDER BY 4 DESC LIMIT 20
    """,
    "seller_ranking": """
        SELECT i.seller_id,COUNT(DISTINCT i.order_id),COUNT(*),SUM(i.price)
        FROM filtered_orders f
        JOIN olist_analytics.order_items i ON i.order_id=f.order_id
        GROUP BY i.seller_id ORDER BY 4 DESC LIMIT 100
    """,
    "order_drilldown_1000": """
        SELECT f.order_id,f.customer_unique_id,f.order_status,v.payment_revenue,
          v.merchandise_value,v.freight_value
        FROM filtered_orders f LEFT JOIN order_revenue v ON v.order_id=f.order_id
        ORDER BY f.order_purchase_timestamp DESC LIMIT 1000
    """,
}

OLD_REPORT = """
    SELECT f.order_id,f.customer_unique_id,f.order_status,
      COALESCE((SELECT SUM(p.payment_value) FROM olist_analytics.order_payments p
                WHERE p.order_id=f.order_id),0) AS payment_revenue,
      COALESCE((SELECT SUM(i.price) FROM olist_analytics.order_items i
                WHERE i.order_id=f.order_id),0) AS merchandise_value,
      COALESCE((SELECT SUM(i.freight_value) FROM olist_analytics.order_items i
                WHERE i.order_id=f.order_id),0) AS freight_value
    FROM filtered_orders f ORDER BY f.order_purchase_timestamp DESC LIMIT 50000
"""

NEW_REPORT = """
    SELECT f.order_id,f.customer_unique_id,f.order_status,
      COALESCE(v.payment_revenue,0),COALESCE(v.merchandise_value,0),
      COALESCE(v.freight_value,0)
    FROM filtered_orders f LEFT JOIN order_revenue v ON v.order_id=f.order_id
    ORDER BY f.order_purchase_timestamp DESC LIMIT 50000
"""


def main() -> None:
    min_date, max_date, _, _ = get_filter_options()
    filters = FilterState(min_date, max_date)
    old_cte, old_params = fallback_orders_cte(filters)
    new_cte, new_params = optimized_cte(filters)
    for name, suffix in COMMON.items():
        before = execution_ms(old_cte, suffix, old_params)
        after = execution_ms(new_cte, suffix, new_params)
        print(f"{name}: before={before:.3f} ms after={after:.3f} ms")
    before = execution_ms(old_cte, OLD_REPORT, old_params)
    after = execution_ms(new_cte, NEW_REPORT, new_params)
    print(f"order_report_50000: before={before:.3f} ms after={after:.3f} ms")


if __name__ == "__main__":
    main()
