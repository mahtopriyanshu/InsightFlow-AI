"""Shared analytics query primitives."""
from datetime import date

import pandas as pd

from streamlit_app.database.connection import query_dataframe
from streamlit_app.utils.filters import FilterState, order_filter_sql


def get_filter_options() -> tuple[date, date, list[str], list[str]]:
    """Load valid global filter values from curated tables."""
    dates = query_dataframe(
        """
        SELECT
            MIN(order_purchase_timestamp)::date AS min_date,
            MAX(order_purchase_timestamp)::date AS max_date
        FROM olist_analytics.orders
        """
    )
    states = query_dataframe(
        """
        SELECT DISTINCT customer_state AS value
        FROM olist_analytics.customers
        ORDER BY value
        """
    )
    categories = query_dataframe(
        """
        SELECT DISTINCT
            COALESCE(t.product_category_name_english, p.product_category_name)
                AS value
        FROM olist_analytics.products AS p
        LEFT JOIN olist_analytics.product_category_translation AS t
            ON t.product_category_name = p.product_category_name
        WHERE COALESCE(
            t.product_category_name_english,
            p.product_category_name
        ) IS NOT NULL
        ORDER BY value
        """
    )
    return (
        dates.iloc[0]["min_date"],
        dates.iloc[0]["max_date"],
        states["value"].tolist(),
        categories["value"].tolist(),
    )


def analytics_serving_available() -> bool:
    """Return whether both validated serving views are present."""
    objects = query_dataframe(
        """
        SELECT
            to_regclass('olist_analytics.vw_order_revenue') IS NOT NULL
                AS revenue_ready,
            to_regclass('olist_analytics.vw_order_delivery_metrics') IS NOT NULL
                AS delivery_ready
        """
    )
    return bool(objects.iloc[0]["revenue_ready"] and objects.iloc[0]["delivery_ready"])


def filtered_orders_cte(
    filters: FilterState,
    *,
    prefer_serving: bool = True,
) -> tuple[str, tuple[object, ...]]:
    """Return filtered order CTEs, preferring validated serving views."""
    predicate, params = order_filter_sql(filters)
    if prefer_serving and analytics_serving_available():
        sql = f"""
            WITH filtered_orders AS (
                SELECT
                    o.order_id, o.customer_id, c.customer_unique_id,
                    c.customer_state, c.customer_city, o.order_status,
                    o.order_purchase_timestamp,
                    o.order_delivered_customer_date,
                    o.order_estimated_delivery_date
                FROM olist_analytics.orders AS o
                JOIN olist_analytics.customers AS c
                    ON c.customer_id = o.customer_id
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
        """
        return sql, params

    return fallback_orders_cte(filters)


def fallback_orders_cte(
    filters: FilterState,
) -> tuple[str, tuple[object, ...]]:
    """Return the validated base-table CTE fallback."""
    predicate, params = order_filter_sql(filters, sargable_dates=False)
    sql = f"""
        WITH filtered_orders AS (
            SELECT
                o.order_id,
                o.customer_id,
                c.customer_unique_id,
                c.customer_state,
                c.customer_city,
                o.order_status,
                o.order_purchase_timestamp,
                o.order_delivered_customer_date,
                o.order_estimated_delivery_date
            FROM olist_analytics.orders AS o
            JOIN olist_analytics.customers AS c
                ON c.customer_id = o.customer_id
            WHERE {predicate}
        ),
        payment_totals AS (
            SELECT order_id, SUM(payment_value) AS payment_revenue
            FROM olist_analytics.order_payments
            GROUP BY order_id
        ),
        item_totals AS (
            SELECT
                order_id,
                SUM(price) AS merchandise_value,
                SUM(freight_value) AS freight_value,
                SUM(price + freight_value) AS total_item_value
            FROM olist_analytics.order_items
            GROUP BY order_id
        ),
        order_revenue AS (
            SELECT
                COALESCE(p.order_id, i.order_id) AS order_id,
                COALESCE(p.payment_revenue, 0) AS payment_revenue,
                COALESCE(i.merchandise_value, 0) AS merchandise_value,
                COALESCE(i.freight_value, 0) AS freight_value,
                COALESCE(i.total_item_value, 0) AS total_item_value
            FROM payment_totals AS p
            FULL JOIN item_totals AS i ON i.order_id = p.order_id
        ),
        delivery_metrics AS (
            SELECT
                order_id,
                CASE
                    WHEN order_delivered_customer_date IS NULL THEN NULL
                    ELSE EXTRACT(EPOCH FROM (
                        order_delivered_customer_date - order_purchase_timestamp
                    )) / 86400.0
                END AS actual_delivery_days,
                CASE
                    WHEN order_delivered_customer_date IS NULL THEN NULL
                    ELSE EXTRACT(EPOCH FROM (
                        order_delivered_customer_date
                        - order_estimated_delivery_date
                    )) / 86400.0
                END AS delivery_delay_days,
                CASE
                    WHEN order_delivered_customer_date IS NULL
                        THEN 'not_delivered'
                    WHEN order_delivered_customer_date
                         > order_estimated_delivery_date
                        THEN 'late'
                    ELSE 'on_time_or_early'
                END AS delivery_performance
            FROM olist_analytics.orders
        )
    """
    return sql, params


