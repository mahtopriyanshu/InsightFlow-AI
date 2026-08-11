"""Equivalence and controlled performance validation for Milestone 10."""
from datetime import date
from pathlib import Path
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from streamlit_app.database.connection import query_dataframe
from streamlit_app.services.common import filtered_orders_cte, get_filter_options
from streamlit_app.utils.filters import FilterState, order_filter_sql


def optimized_cte(filters: FilterState) -> tuple[str, tuple[object, ...]]:
    predicate, params = order_filter_sql(filters)
    return f"""
        WITH filtered_orders AS (
            SELECT o.order_id, o.customer_id, c.customer_unique_id,
                c.customer_state, c.customer_city, o.order_status,
                o.order_purchase_timestamp, o.order_delivered_customer_date,
                o.order_estimated_delivery_date
            FROM olist_analytics.orders AS o
            JOIN olist_analytics.customers AS c ON c.customer_id=o.customer_id
            WHERE {predicate}
        ),
        order_revenue AS (
            SELECT order_id, payment_revenue, merchandise_value,
                freight_value, total_item_value
            FROM olist_analytics.vw_order_revenue
        ),
        delivery_metrics AS (
            SELECT order_id, actual_delivery_days, delivery_delay_days,
                delivery_performance
            FROM olist_analytics.vw_order_delivery_metrics
        )
    """, params


QUERIES = {
    "executive": """
        , review_scores AS (
          SELECT AVG(r.review_score) AS average_review_score
          FROM olist_analytics.order_reviews r
          JOIN filtered_orders f ON f.order_id=r.order_id)
        SELECT COALESCE(SUM(v.payment_revenue),0) AS total_revenue,
          COUNT(*) AS total_orders,
          COUNT(DISTINCT f.customer_unique_id) AS unique_customers,
          COALESCE(AVG(v.payment_revenue),0) AS average_order_value,
          MAX(rs.average_review_score) AS average_review_score,
          100.0*SUM(CASE WHEN f.order_status='delivered' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*),0) AS delivery_rate
        FROM filtered_orders f LEFT JOIN order_revenue v ON v.order_id=f.order_id
        CROSS JOIN review_scores rs
    """,
    "delivery": """
        SELECT AVG(d.actual_delivery_days) AS average_delivery_days,
          100.0*SUM(CASE WHEN d.delivery_performance='late' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*) FILTER (WHERE d.delivery_performance<>'not_delivered'),0) AS late_rate,
          AVG(v.freight_value) AS average_freight
        FROM filtered_orders f JOIN delivery_metrics d ON d.order_id=f.order_id
        LEFT JOIN order_revenue v ON v.order_id=f.order_id
    """,
    "customer_top": """
        SELECT f.customer_unique_id,MIN(f.customer_state) AS state,
          COUNT(*) AS orders,SUM(COALESCE(v.payment_revenue,0)) AS revenue
        FROM filtered_orders f LEFT JOIN order_revenue v ON v.order_id=f.order_id
        GROUP BY f.customer_unique_id
        ORDER BY revenue DESC, f.customer_unique_id LIMIT 25
    """,
}


def assert_equivalent(name: str, old: pd.DataFrame, new: pd.DataFrame) -> None:
    pd.testing.assert_frame_equal(
        old.reset_index(drop=True), new.reset_index(drop=True),
        check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-9,
    )
    print(f"PASS {name}: {len(old):,} rows")


def execution_ms(cte: str, suffix: str, params: tuple[object, ...]) -> float:
    plan = query_dataframe(
        "EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) " + cte + suffix, params
    ).iloc[:, 0].astype(str)
    line = next(value for value in plan if value.startswith("Execution Time:"))
    return float(re.search(r"([0-9.]+) ms", line).group(1))


def main() -> None:
    min_date, max_date, states, categories = get_filter_options()
    category = "health_beauty" if "health_beauty" in categories else categories[0]
    contexts = {
        "full": FilterState(min_date, max_date),
        "date": FilterState(date(2018, 1, 1), date(2018, 6, 30)),
        "state": FilterState(min_date, max_date, ("SP",)),
        "category": FilterState(min_date, max_date, (), (category,)),
        "combined": FilterState(date(2018, 1, 1), date(2018, 6, 30), ("SP",), (category,)),
    }
    for context, filters in contexts.items():
        old_cte, old_params = filtered_orders_cte(filters, prefer_serving=False)
        new_cte, new_params = optimized_cte(filters)
        for metric, suffix in QUERIES.items():
            assert_equivalent(
                f"{context}.{metric}",
                query_dataframe(old_cte + suffix, old_params),
                query_dataframe(new_cte + suffix, new_params),
            )
    print("--- CONTROLLED PERFORMANCE COMPARISON (FULL) ---")
    old_cte, old_params = filtered_orders_cte(contexts["full"], prefer_serving=False)
    new_cte, new_params = optimized_cte(contexts["full"])
    for metric, suffix in QUERIES.items():
        before = execution_ms(old_cte, suffix, old_params)
        after = execution_ms(new_cte, suffix, new_params)
        print(f"{metric}: before={before:.3f} ms after={after:.3f} ms")


if __name__ == "__main__":
    main()
