"""Executive overview analytics."""
import pandas as pd

from streamlit_app.database.connection import query_dataframe
from streamlit_app.services.common import analytics_serving_available, filtered_orders_cte
from streamlit_app.utils.filters import FilterState


def get_kpis(filters: FilterState) -> pd.DataFrame:
    """Return executive KPIs for the active filter context."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        , review_scores AS (
            SELECT AVG(r.review_score) AS average_review_score
            FROM olist_analytics.order_reviews AS r
            JOIN filtered_orders AS f ON f.order_id = r.order_id
        )
        SELECT
            COALESCE(SUM(v.payment_revenue), 0) AS total_revenue,
            COUNT(*) AS total_orders,
            COUNT(DISTINCT f.customer_unique_id) AS unique_customers,
            COALESCE(AVG(v.payment_revenue), 0) AS average_order_value,
            MAX(rs.average_review_score) AS average_review_score,
            100.0 * SUM(CASE WHEN f.order_status = 'delivered' THEN 1 ELSE 0 END)
                / NULLIF(COUNT(*), 0) AS delivery_rate
        FROM filtered_orders AS f
        LEFT JOIN order_revenue AS v
            ON v.order_id = f.order_id
        CROSS JOIN review_scores AS rs
        """,
        params,
    )


def get_monthly_performance(filters: FilterState) -> pd.DataFrame:
    """Return monthly revenue, order count, and AOV."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT
            date_trunc('month', f.order_purchase_timestamp)::date AS month,
            COUNT(*) AS orders,
            COALESCE(SUM(v.payment_revenue), 0) AS revenue,
            COALESCE(AVG(v.payment_revenue), 0) AS average_order_value
        FROM filtered_orders AS f
        LEFT JOIN order_revenue AS v
            ON v.order_id = f.order_id
        GROUP BY date_trunc('month', f.order_purchase_timestamp)
        ORDER BY month
        """,
        params,
    )


def get_category_performance(
    filters: FilterState,
    limit: int = 12,
) -> pd.DataFrame:
    """Return category merchandise revenue and order volume."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT
            COALESCE(t.product_category_name_english, p.product_category_name)
                AS category,
            COUNT(DISTINCT i.order_id) AS orders,
            COUNT(*) AS items_sold,
            SUM(i.price) AS revenue,
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
        ORDER BY revenue DESC
        LIMIT %s
        """,
        (*params, limit),
    )


def get_status_distribution(filters: FilterState) -> pd.DataFrame:
    """Return order status distribution."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT order_status, COUNT(*) AS orders
        FROM filtered_orders
        GROUP BY order_status
        ORDER BY orders DESC
        """,
        params,
    )


def get_state_performance(filters: FilterState) -> pd.DataFrame:
    """Return state-level revenue and customer performance."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT
            f.customer_state AS state,
            COUNT(*) AS orders,
            COUNT(DISTINCT f.customer_unique_id) AS customers,
            COALESCE(SUM(v.payment_revenue), 0) AS revenue
        FROM filtered_orders AS f
        LEFT JOIN order_revenue AS v
            ON v.order_id = f.order_id
        GROUP BY f.customer_state
        ORDER BY revenue DESC
        """,
        params,
    )


def get_payment_methods(filters: FilterState) -> pd.DataFrame:
    """Return payment-method usage for filtered orders."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT
            p.payment_type,
            COUNT(*) AS payment_records,
            COUNT(DISTINCT p.order_id) AS orders,
            SUM(p.payment_value) AS payment_value
        FROM olist_analytics.order_payments AS p
        JOIN filtered_orders AS f ON f.order_id = p.order_id
        GROUP BY p.payment_type
        ORDER BY payment_value DESC
        """,
        params,
    )


def get_order_details(
    filters: FilterState,
    limit: int = 1000,
) -> pd.DataFrame:
    """Return drillable filtered order-level facts."""
    cte, params = filtered_orders_cte(filters)
    if analytics_serving_available():
        detail_sql = """
        SELECT
            f.order_id, f.customer_unique_id, f.customer_state,
            f.order_status, f.order_purchase_timestamp,
            COALESCE(v.payment_revenue, 0) AS payment_revenue,
            COALESCE(v.merchandise_value, 0) AS merchandise_value,
            COALESCE(v.freight_value, 0) AS freight_value
        FROM filtered_orders AS f
        LEFT JOIN order_revenue AS v ON v.order_id = f.order_id
        ORDER BY f.order_purchase_timestamp DESC, f.order_id
        LIMIT %s
        """
    else:
        detail_sql = """
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
            ), 0) AS freight_value
        FROM filtered_orders AS f
        ORDER BY f.order_purchase_timestamp DESC, f.order_id
        LIMIT %s
        """
    return query_dataframe(cte + detail_sql, (*params, limit))


def get_sales_summary(filters: FilterState) -> pd.DataFrame:
    """Return supported commercial headline metrics in one filtered query."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(cte + """
        SELECT COALESCE(SUM(v.payment_revenue),0) AS total_revenue,
            COUNT(*) AS total_orders,
            COALESCE(AVG(v.payment_revenue),0) AS average_order_value,
            COALESCE(SUM(i.item_count),0) AS items_sold,
            100.0 * SUM(CASE WHEN f.order_status='canceled' THEN 1 ELSE 0 END)
              / NULLIF(COUNT(*),0) AS cancellation_rate
        FROM filtered_orders AS f
        LEFT JOIN order_revenue AS v ON v.order_id=f.order_id
        LEFT JOIN (SELECT order_id,COUNT(*) AS item_count
                   FROM olist_analytics.order_items GROUP BY order_id) AS i
          ON i.order_id=f.order_id
    """, params)


def get_customer_mix(filters: FilterState) -> pd.DataFrame:
    """Return evidence-based one-time versus repeat customer counts."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(cte + """
        , customer_counts AS (
          SELECT customer_unique_id,COUNT(*) AS orders
          FROM filtered_orders GROUP BY customer_unique_id)
        SELECT CASE WHEN orders>1 THEN 'Repeat customers' ELSE 'One-time customers' END AS customer_type,
               COUNT(*) AS customers
        FROM customer_counts GROUP BY 1 ORDER BY customers DESC
    """, params)


def get_delivery_outcomes(filters: FilterState) -> pd.DataFrame:
    """Return aggregate delivered-order promise-date outcomes."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(cte + """
        SELECT CASE WHEN d.delivery_performance='late' THEN 'Late'
                    ELSE 'On time / early' END AS delivery_outcome,
               COUNT(*) AS orders
        FROM filtered_orders AS f
        JOIN delivery_metrics AS d ON d.order_id=f.order_id
        WHERE d.delivery_performance<>'not_delivered'
        GROUP BY 1 ORDER BY orders DESC
    """, params)
