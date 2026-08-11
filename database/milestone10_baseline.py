"""Capture reproducible KPI and query-plan baselines for Milestone 10."""
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit_app.database.connection import query_dataframe
from streamlit_app.services.common import filtered_orders_cte, get_filter_options
from streamlit_app.services.customers import get_customer_metrics
from streamlit_app.services.commerce import get_seller_performance
from streamlit_app.services.operations import get_delivery_metrics, get_review_metrics
from streamlit_app.services.overview import (
    get_category_performance, get_kpis, get_state_performance,
)
from streamlit_app.utils.filters import FilterState


def _json_value(value):
    if isinstance(value, (Decimal, date)):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def snapshot(filters: FilterState) -> dict:
    kpi = get_kpis(filters).iloc[0]
    delivery = get_delivery_metrics(filters).iloc[0]
    customer = get_customer_metrics(filters).iloc[0]
    review = get_review_metrics(filters).iloc[0]
    categories = get_category_performance(filters, 1)
    states = get_state_performance(filters).head(1)
    sellers = get_seller_performance(filters, 1)
    result = {
        "filters": filters.__dict__,
        "total_revenue": kpi["total_revenue"],
        "total_orders": kpi["total_orders"],
        "unique_customers": kpi["unique_customers"],
        "average_order_value": kpi["average_order_value"],
        "delivery_rate": kpi["delivery_rate"],
        "late_delivery_rate": delivery["late_rate"],
        "average_delivery_days": delivery["average_delivery_days"],
        "average_review_score": review["average_review_score"],
        "negative_review_rate": review["negative_review_rate"],
        "repeat_customer_rate": customer["repeat_rate"],
        "top_revenue_category": None if categories.empty else categories.iloc[0].to_dict(),
        "top_revenue_state": None if states.empty else states.iloc[0].to_dict(),
        "top_seller": None if sellers.empty else sellers.iloc[0].to_dict(),
    }
    return result


def explain_baselines(filters: FilterState) -> dict[str, list[str]]:
    cte, params = filtered_orders_cte(filters)
    queries = {
        "executive_kpis": cte + """
            SELECT COALESCE(SUM(v.payment_revenue),0), COUNT(*),
                   COUNT(DISTINCT f.customer_unique_id),
                   COALESCE(AVG(v.payment_revenue),0)
            FROM filtered_orders f
            LEFT JOIN order_revenue v ON v.order_id=f.order_id
        """,
        "category_ranking": cte + """
            SELECT COALESCE(t.product_category_name_english,p.product_category_name),
                   COUNT(DISTINCT i.order_id),SUM(i.price)
            FROM filtered_orders f
            JOIN olist_analytics.order_items i ON i.order_id=f.order_id
            JOIN olist_analytics.products p ON p.product_id=i.product_id
            LEFT JOIN olist_analytics.product_category_translation t
              ON t.product_category_name=p.product_category_name
            GROUP BY 1 ORDER BY 3 DESC LIMIT 20
        """,
        "seller_ranking": cte + """
            SELECT i.seller_id,COUNT(DISTINCT i.order_id),SUM(i.price)
            FROM filtered_orders f
            JOIN olist_analytics.order_items i ON i.order_id=f.order_id
            GROUP BY i.seller_id ORDER BY 3 DESC LIMIT 100
        """,
        "customer_summary": cte + """
            SELECT f.customer_unique_id,COUNT(*),SUM(COALESCE(v.payment_revenue,0))
            FROM filtered_orders f
            LEFT JOIN order_revenue v ON v.order_id=f.order_id
            GROUP BY f.customer_unique_id ORDER BY 3 DESC LIMIT 25
        """,
    }
    plans = {}
    for name, sql in queries.items():
        frame = query_dataframe(
            "EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) " + sql, params
        )
        plans[name] = frame.iloc[:, 0].astype(str).tolist()
    return plans


def main() -> None:
    min_date, max_date, states, categories = get_filter_options()
    category = "health_beauty" if "health_beauty" in categories else categories[0]
    contexts = {
        "full": FilterState(min_date, max_date),
        "date_range": FilterState(date(2018, 1, 1), date(2018, 6, 30)),
        "state": FilterState(min_date, max_date, ("SP",)),
        "category": FilterState(min_date, max_date, (), (category,)),
        "combined": FilterState(date(2018, 1, 1), date(2018, 6, 30), ("SP",), (category,)),
    }
    output = {name: snapshot(filters) for name, filters in contexts.items()}
    print("--- KPI BASELINES ---")
    print(json.dumps(output, default=_json_value, indent=2))
    print("--- EXPLAIN BASELINES (FULL DATASET) ---")
    for name, lines in explain_baselines(contexts["full"]).items():
        print(f"### {name}")
        print("\n".join(lines))


if __name__ == "__main__":
    main()
