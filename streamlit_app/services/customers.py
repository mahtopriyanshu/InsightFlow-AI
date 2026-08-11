"""Customer intelligence queries."""
import pandas as pd

from streamlit_app.database.connection import query_dataframe
from streamlit_app.services.common import filtered_orders_cte
from streamlit_app.utils.filters import FilterState


def get_customer_metrics(filters: FilterState) -> pd.DataFrame:
    """Return unique, repeat, and average customer metrics."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        , customer_orders AS (
            SELECT
                customer_unique_id,
                COUNT(*) AS order_count,
                SUM(COALESCE(v.payment_revenue, 0)) AS revenue
            FROM filtered_orders AS f
            LEFT JOIN order_revenue AS v
                ON v.order_id = f.order_id
            GROUP BY customer_unique_id
        )
        SELECT
            COUNT(*) AS unique_customers,
            SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END)
                AS repeat_customers,
            100.0 * SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END)
                / NULLIF(COUNT(*), 0) AS repeat_rate,
            AVG(order_count) AS orders_per_customer,
            AVG(revenue) AS revenue_per_customer
        FROM customer_orders
        """,
        params,
    )


def get_customer_locations(filters: FilterState) -> pd.DataFrame:
    """Return customer and order distribution by state and city."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT
            customer_state AS state,
            customer_city AS city,
            COUNT(DISTINCT customer_unique_id) AS customers,
            COUNT(*) AS orders
        FROM filtered_orders
        GROUP BY customer_state, customer_city
        ORDER BY orders DESC
        """,
        params,
    )


def get_top_customers(filters: FilterState, limit: int = 25) -> pd.DataFrame:
    """Return highest-value repeat customer profiles."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT
            f.customer_unique_id,
            MIN(f.customer_state) AS state,
            COUNT(*) AS orders,
            SUM(COALESCE(v.payment_revenue, 0)) AS revenue,
            MIN(f.order_purchase_timestamp) AS first_order,
            MAX(f.order_purchase_timestamp) AS last_order
        FROM filtered_orders AS f
        LEFT JOIN order_revenue AS v
            ON v.order_id = f.order_id
        GROUP BY f.customer_unique_id
        ORDER BY revenue DESC, f.customer_unique_id
        LIMIT %s
        """,
        (*params, limit),
    )


def search_customers(search_term: str, limit: int = 30) -> pd.DataFrame:
    """Search stable customer identifiers by prefix or substring."""
    return query_dataframe(
        """
        WITH payment_totals AS (
            SELECT order_id, SUM(payment_value) AS payment_revenue
            FROM olist_analytics.order_payments
            GROUP BY order_id
        )
        SELECT
            c.customer_unique_id,
            MIN(c.customer_state) AS customer_state,
            MIN(c.customer_city) AS customer_city,
            COUNT(DISTINCT o.order_id) AS order_count,
            COALESCE(SUM(p.payment_revenue), 0) AS total_revenue,
            COALESCE(AVG(p.payment_revenue), 0) AS average_order_value,
            MIN(o.order_purchase_timestamp) AS first_order_at,
            MAX(o.order_purchase_timestamp) AS last_order_at
        FROM olist_analytics.customers AS c
        LEFT JOIN olist_analytics.orders AS o ON o.customer_id = c.customer_id
        LEFT JOIN payment_totals AS p ON p.order_id = o.order_id
        WHERE c.customer_unique_id ILIKE %s
        GROUP BY c.customer_unique_id
        ORDER BY total_revenue DESC
        LIMIT %s
        """,
        (f"%{search_term.strip()}%", limit),
    )


def get_customer_orders(customer_unique_id: str) -> pd.DataFrame:
    """Return complete order history for one stable customer."""
    return query_dataframe(
        """
        WITH payment_totals AS (
            SELECT order_id, SUM(payment_value) AS payment_revenue
            FROM olist_analytics.order_payments
            GROUP BY order_id
        ),
        item_totals AS (
            SELECT
                order_id,
                SUM(price) AS merchandise_value,
                SUM(freight_value) AS freight_value
            FROM olist_analytics.order_items
            GROUP BY order_id
        )
        SELECT
            o.order_id,
            o.order_purchase_timestamp,
            o.order_status,
            COALESCE(p.payment_revenue, 0) AS payment_revenue,
            COALESCE(i.merchandise_value, 0) AS merchandise_value,
            COALESCE(i.freight_value, 0) AS freight_value,
            CASE
                WHEN o.order_delivered_customer_date IS NULL THEN NULL
                ELSE EXTRACT(EPOCH FROM (
                    o.order_delivered_customer_date - o.order_purchase_timestamp
                )) / 86400.0
            END AS actual_delivery_days,
            CASE
                WHEN o.order_delivered_customer_date IS NULL THEN 'not_delivered'
                WHEN o.order_delivered_customer_date
                     > o.order_estimated_delivery_date THEN 'late'
                ELSE 'on_time_or_early'
            END AS delivery_performance
        FROM olist_analytics.customers AS c
        JOIN olist_analytics.orders AS o ON o.customer_id = c.customer_id
        LEFT JOIN payment_totals AS p ON p.order_id = o.order_id
        LEFT JOIN item_totals AS i ON i.order_id = o.order_id
        WHERE c.customer_unique_id = %s
        ORDER BY o.order_purchase_timestamp DESC
        """,
        (customer_unique_id,),
    )
