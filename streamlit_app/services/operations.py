"""Delivery and review analytics queries."""
import pandas as pd

from streamlit_app.database.connection import query_dataframe
from streamlit_app.services.common import filtered_orders_cte
from streamlit_app.utils.filters import FilterState


def get_delivery_metrics(filters: FilterState) -> pd.DataFrame:
    """Return headline delivery metrics."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT
            100.0 * SUM(CASE WHEN f.order_status = 'delivered' THEN 1 ELSE 0 END)
                / NULLIF(COUNT(*), 0) AS delivery_rate,
            SUM(CASE WHEN f.order_status = 'delivered' THEN 1 ELSE 0 END) AS delivered_orders,
            100.0 * SUM(CASE WHEN f.order_status = 'canceled' THEN 1 ELSE 0 END)
                / NULLIF(COUNT(*), 0) AS cancellation_rate,
            AVG(d.actual_delivery_days) AS average_delivery_days,
            100.0 * SUM(CASE WHEN d.delivery_performance = 'late' THEN 1 ELSE 0 END)
                / NULLIF(SUM(CASE
                    WHEN d.delivery_performance <> 'not_delivered' THEN 1 ELSE 0
                END), 0) AS late_rate,
            AVG(CASE
                WHEN d.delivery_delay_days > 0 THEN d.delivery_delay_days
            END) AS average_late_days,
            AVG(v.freight_value) AS average_freight
        FROM filtered_orders AS f
        JOIN delivery_metrics AS d
            ON d.order_id = f.order_id
        LEFT JOIN order_revenue AS v
            ON v.order_id = f.order_id
        """,
        params,
    )


def get_delivery_by_state(filters: FilterState) -> pd.DataFrame:
    """Return delivery performance by customer state."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT
            f.customer_state AS state,
            COUNT(*) FILTER (
                WHERE d.delivery_performance <> 'not_delivered'
            ) AS delivered_orders,
            AVG(d.actual_delivery_days) AS average_delivery_days,
            100.0 * SUM(CASE WHEN d.delivery_performance = 'late' THEN 1 ELSE 0 END)
                / NULLIF(COUNT(*) FILTER (
                    WHERE d.delivery_performance <> 'not_delivered'
                ), 0) AS late_rate,
            AVG(v.freight_value) AS average_freight
        FROM filtered_orders AS f
        JOIN delivery_metrics AS d
            ON d.order_id = f.order_id
        LEFT JOIN order_revenue AS v
            ON v.order_id = f.order_id
        GROUP BY f.customer_state
        ORDER BY late_rate DESC NULLS LAST
        """,
        params,
    )


def get_delivery_trend(filters: FilterState) -> pd.DataFrame:
    """Return monthly delivery speed and late-rate trend."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte + """
        SELECT date_trunc('month', f.order_purchase_timestamp)::date AS month,
            AVG(d.actual_delivery_days) AS average_delivery_days,
            100.0 * SUM(CASE WHEN d.delivery_performance = 'late' THEN 1 ELSE 0 END)
              / NULLIF(COUNT(*) FILTER (WHERE d.delivery_performance <> 'not_delivered'), 0) AS late_rate
        FROM filtered_orders AS f
        JOIN delivery_metrics AS d ON d.order_id = f.order_id
        GROUP BY 1 ORDER BY 1
        """, params)


def get_delivery_distribution(filters: FilterState) -> pd.DataFrame:
    """Return order-level delivery durations for distribution analysis."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT
            d.order_id,
            d.actual_delivery_days,
            d.delivery_delay_days,
            d.delivery_performance
        FROM filtered_orders AS f
        JOIN delivery_metrics AS d
            ON d.order_id = f.order_id
        WHERE d.actual_delivery_days IS NOT NULL
        """,
        params,
    )


def get_review_metrics(filters: FilterState) -> pd.DataFrame:
    """Return average and negative-review metrics."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT
            AVG(r.review_score) AS average_review_score,
            COUNT(*) AS total_reviews,
            SUM(CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END)
                AS negative_reviews,
            100.0 * SUM(CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END)
                / NULLIF(COUNT(*), 0) AS negative_review_rate
        FROM filtered_orders AS f
        JOIN olist_analytics.order_reviews AS r ON r.order_id = f.order_id
        """,
        params,
    )


def get_review_distribution(filters: FilterState) -> pd.DataFrame:
    """Return review score distribution."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT r.review_score, COUNT(*) AS reviews
        FROM filtered_orders AS f
        JOIN olist_analytics.order_reviews AS r ON r.order_id = f.order_id
        GROUP BY r.review_score
        ORDER BY r.review_score
        """,
        params,
    )


def get_review_trend(filters: FilterState) -> pd.DataFrame:
    """Return monthly review score and volume."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT
            date_trunc('month', r.review_creation_date)::date AS month,
            AVG(r.review_score) AS average_review_score,
            COUNT(*) AS reviews
        FROM filtered_orders AS f
        JOIN olist_analytics.order_reviews AS r ON r.order_id = f.order_id
        GROUP BY date_trunc('month', r.review_creation_date)
        ORDER BY month
        """,
        params,
    )


def get_review_by_category(filters: FilterState, limit: int = 20) -> pd.DataFrame:
    """Return category review performance without duplicate review/category rows."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        , category_reviews AS (
            SELECT DISTINCT
                r.review_id,
                r.order_id,
                r.review_score,
                COALESCE(t.product_category_name_english, p.product_category_name)
                    AS category
            FROM filtered_orders AS f
            JOIN olist_analytics.order_reviews AS r ON r.order_id = f.order_id
            JOIN olist_analytics.order_items AS i ON i.order_id = f.order_id
            JOIN olist_analytics.products AS p ON p.product_id = i.product_id
            LEFT JOIN olist_analytics.product_category_translation AS t
                ON t.product_category_name = p.product_category_name
        )
        SELECT
            category,
            COUNT(*) AS reviews,
            AVG(review_score) AS average_review_score
        FROM category_reviews
        GROUP BY category
        HAVING COUNT(*) >= 25
        ORDER BY average_review_score DESC, reviews DESC
        LIMIT %s
        """,
        (*params, limit),
    )


def get_delivery_review_relationship(filters: FilterState) -> pd.DataFrame:
    """Compare customer ratings by delivery outcome."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT
            d.delivery_performance,
            COUNT(*) AS reviews,
            AVG(r.review_score) AS average_review_score
        FROM filtered_orders AS f
        JOIN delivery_metrics AS d
            ON d.order_id = f.order_id
        JOIN olist_analytics.order_reviews AS r ON r.order_id = f.order_id
        GROUP BY d.delivery_performance
        ORDER BY average_review_score DESC
        """,
        params,
    )


def get_negative_reviews(filters: FilterState, limit: int = 250) -> pd.DataFrame:
    """Return recent low-score reviews for operational follow-up."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT
            r.review_id,
            r.order_id,
            r.review_score,
            r.review_creation_date,
            r.review_comment_title,
            r.review_comment_message,
            d.delivery_performance,
            d.delivery_delay_days
        FROM filtered_orders AS f
        JOIN olist_analytics.order_reviews AS r ON r.order_id = f.order_id
        LEFT JOIN delivery_metrics AS d
            ON d.order_id = f.order_id
        WHERE r.review_score <= 2
        ORDER BY r.review_creation_date DESC
        LIMIT %s
        """,
        (*params, limit),
    )

