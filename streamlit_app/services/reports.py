"""Downloadable filtered report datasets."""
import pandas as pd

from streamlit_app.database.connection import query_dataframe
from streamlit_app.services.common import analytics_serving_available, filtered_orders_cte
from streamlit_app.utils.filters import FilterState


def get_report_dataset(
    report_name: str,
    filters: FilterState,
    limit: int = 50000,
) -> pd.DataFrame:
    """Return a controlled report dataset selected by a trusted key."""
    cte, params = filtered_orders_cte(filters)
    if analytics_serving_available():
        order_performance_sql = """
            SELECT
                f.order_id, f.customer_unique_id, f.customer_state,
                f.order_status, f.order_purchase_timestamp,
                COALESCE(v.payment_revenue, 0) AS payment_revenue,
                COALESCE(v.merchandise_value, 0) AS merchandise_value,
                COALESCE(v.freight_value, 0) AS freight_value,
                d.actual_delivery_days, d.delivery_delay_days,
                d.delivery_performance
            FROM filtered_orders AS f
            LEFT JOIN order_revenue AS v ON v.order_id = f.order_id
            LEFT JOIN delivery_metrics AS d ON d.order_id = f.order_id
            ORDER BY f.order_purchase_timestamp DESC, f.order_id
            LIMIT %s
        """
    else:
        order_performance_sql = """
            SELECT
                f.order_id,
                f.customer_unique_id,
                f.customer_state,
                f.order_status,
                f.order_purchase_timestamp,
                COALESCE((
                    SELECT SUM(p.payment_value)
                    FROM olist_analytics.order_payments AS p
                    WHERE p.order_id = f.order_id
                ), 0) AS payment_revenue,
                COALESCE((
                    SELECT SUM(i.price)
                    FROM olist_analytics.order_items AS i
                    WHERE i.order_id = f.order_id
                ), 0) AS merchandise_value,
                COALESCE((
                    SELECT SUM(i.freight_value)
                    FROM olist_analytics.order_items AS i
                    WHERE i.order_id = f.order_id
                ), 0) AS freight_value,
                CASE WHEN f.order_delivered_customer_date IS NULL THEN NULL
                     ELSE EXTRACT(EPOCH FROM (f.order_delivered_customer_date
                          - f.order_purchase_timestamp)) / 86400.0 END
                    AS actual_delivery_days,
                CASE WHEN f.order_delivered_customer_date IS NULL THEN NULL
                     ELSE EXTRACT(EPOCH FROM (f.order_delivered_customer_date
                          - f.order_estimated_delivery_date)) / 86400.0 END
                    AS delivery_delay_days,
                CASE WHEN f.order_delivered_customer_date IS NULL THEN 'not_delivered'
                     WHEN f.order_delivered_customer_date > f.order_estimated_delivery_date
                          THEN 'late' ELSE 'on_time_or_early' END
                    AS delivery_performance
            FROM filtered_orders AS f
            ORDER BY f.order_purchase_timestamp DESC, f.order_id
            LIMIT %s
        """
    queries = {
        "Order performance": order_performance_sql,
        "Customer summary": """
            SELECT
                f.customer_unique_id,
                MIN(f.customer_state) AS customer_state,
                MIN(f.customer_city) AS customer_city,
                COUNT(*) AS order_count,
                SUM(COALESCE(v.payment_revenue, 0)) AS total_revenue,
                MIN(f.order_purchase_timestamp) AS first_order,
                MAX(f.order_purchase_timestamp) AS last_order
            FROM filtered_orders AS f
            LEFT JOIN order_revenue AS v
                ON v.order_id = f.order_id
            GROUP BY f.customer_unique_id
            ORDER BY total_revenue DESC, f.customer_unique_id
            LIMIT %s
        """,
        "Seller performance": """
            SELECT
                s.seller_id,
                s.seller_state,
                s.seller_city,
                COUNT(DISTINCT i.order_id) AS order_count,
                COUNT(*) AS items_sold,
                SUM(i.price) AS merchandise_revenue,
                SUM(i.freight_value) AS freight_value
            FROM filtered_orders AS f
            JOIN olist_analytics.order_items AS i ON i.order_id = f.order_id
            JOIN olist_analytics.sellers AS s ON s.seller_id = i.seller_id
            GROUP BY s.seller_id, s.seller_state, s.seller_city
            ORDER BY merchandise_revenue DESC
            LIMIT %s
        """,
        "Category performance": """
            SELECT
                COALESCE(t.product_category_name_english, p.product_category_name)
                    AS category,
                COUNT(DISTINCT i.order_id) AS orders,
                COUNT(*) AS items_sold,
                SUM(i.price) AS merchandise_revenue,
                AVG(i.freight_value) AS average_freight
            FROM filtered_orders AS f
            JOIN olist_analytics.order_items AS i ON i.order_id = f.order_id
            JOIN olist_analytics.products AS p ON p.product_id = i.product_id
            LEFT JOIN olist_analytics.product_category_translation AS t
                ON t.product_category_name = p.product_category_name
            GROUP BY COALESCE(
                t.product_category_name_english,
                p.product_category_name
            )
            ORDER BY merchandise_revenue DESC
            LIMIT %s
        """,
    }
    if report_name not in queries:
        raise ValueError(f"Unsupported report: {report_name}")
    return query_dataframe(cte + queries[report_name], (*params, limit))


