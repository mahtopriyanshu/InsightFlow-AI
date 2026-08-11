"""Product and seller intelligence queries."""
import pandas as pd

from streamlit_app.database.connection import query_dataframe
from streamlit_app.services.common import filtered_orders_cte
from streamlit_app.utils.filters import FilterState


def get_product_performance(filters: FilterState, limit: int = 30) -> pd.DataFrame:
    """Return category commercial, freight, and review metrics."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        , category_reviews AS (
            SELECT
                COALESCE(t.product_category_name_english, p.product_category_name)
                    AS category,
                AVG(r.review_score) AS average_review_score
            FROM filtered_orders AS f
            JOIN olist_analytics.order_reviews AS r ON r.order_id = f.order_id
            JOIN olist_analytics.order_items AS i ON i.order_id = f.order_id
            JOIN olist_analytics.products AS p ON p.product_id = i.product_id
            LEFT JOIN olist_analytics.product_category_translation AS t
                ON t.product_category_name = p.product_category_name
            GROUP BY COALESCE(
                t.product_category_name_english,
                p.product_category_name
            )
        )
        SELECT
            COALESCE(t.product_category_name_english, p.product_category_name)
                AS category,
            COUNT(DISTINCT p.product_id) AS products,
            COUNT(DISTINCT i.order_id) AS orders,
            COUNT(*) AS items_sold,
            SUM(i.price) AS revenue,
            AVG(i.freight_value) AS average_freight,
            MAX(cr.average_review_score) AS average_review_score
        FROM filtered_orders AS f
        JOIN olist_analytics.order_items AS i ON i.order_id = f.order_id
        JOIN olist_analytics.products AS p ON p.product_id = i.product_id
        LEFT JOIN olist_analytics.product_category_translation AS t
            ON t.product_category_name = p.product_category_name
        LEFT JOIN category_reviews AS cr
            ON cr.category = COALESCE(
                t.product_category_name_english,
                p.product_category_name
            )
        GROUP BY COALESCE(
            t.product_category_name_english,
            p.product_category_name
        )
        ORDER BY revenue DESC
        LIMIT %s
        """,
        (*params, limit),
    )


def search_products(search_term: str, limit: int = 100) -> pd.DataFrame:
    """Search product identifiers and translated categories."""
    return query_dataframe(
        """
        SELECT
            p.product_id,
            COALESCE(t.product_category_name_english, p.product_category_name)
                AS category,
            p.product_weight_g,
            p.product_length_cm,
            p.product_height_cm,
            p.product_width_cm,
            COUNT(i.order_item_id) AS items_sold,
            COALESCE(SUM(i.price), 0) AS revenue
        FROM olist_analytics.products AS p
        LEFT JOIN olist_analytics.product_category_translation AS t
            ON t.product_category_name = p.product_category_name
        LEFT JOIN olist_analytics.order_items AS i
            ON i.product_id = p.product_id
        WHERE p.product_id ILIKE %s
           OR COALESCE(t.product_category_name_english, p.product_category_name)
              ILIKE %s
        GROUP BY p.product_id, category
        ORDER BY revenue DESC
        LIMIT %s
        """,
        (f"%{search_term.strip()}%", f"%{search_term.strip()}%", limit),
    )


def get_seller_performance(filters: FilterState, limit: int = 100) -> pd.DataFrame:
    """Return seller sales and fulfilment metrics."""
    cte, params = filtered_orders_cte(filters)
    return query_dataframe(
        cte
        + """
        SELECT
            s.seller_id,
            s.seller_state AS state,
            s.seller_city AS city,
            COUNT(DISTINCT i.order_id) AS orders,
            COUNT(*) AS items_sold,
            SUM(i.price) AS revenue,
            AVG(i.price) AS average_item_value,
            100.0 * COUNT(DISTINCT CASE
                WHEN f.order_status = 'delivered' THEN i.order_id
            END) / NULLIF(COUNT(DISTINCT i.order_id), 0) AS delivery_rate
        FROM filtered_orders AS f
        JOIN olist_analytics.order_items AS i ON i.order_id = f.order_id
        JOIN olist_analytics.sellers AS s ON s.seller_id = i.seller_id
        GROUP BY s.seller_id, s.seller_state, s.seller_city
        ORDER BY revenue DESC
        LIMIT %s
        """,
        (*params, limit),
    )


def search_sellers(search_term: str, limit: int = 50) -> pd.DataFrame:
    """Search seller identifiers and locations."""
    return query_dataframe(
        """
        SELECT
            s.seller_id,
            s.seller_state,
            s.seller_city,
            COUNT(DISTINCT i.order_id) AS order_count,
            COUNT(i.order_item_id) AS items_sold,
            COALESCE(SUM(i.price), 0) AS merchandise_revenue,
            COALESCE(SUM(i.freight_value), 0) AS freight_value,
            COUNT(DISTINCT CASE
                WHEN o.order_status = 'delivered' THEN i.order_id
            END) AS delivered_orders,
            COUNT(DISTINCT CASE
                WHEN o.order_status = 'canceled' THEN i.order_id
            END) AS cancelled_orders
        FROM olist_analytics.sellers AS s
        LEFT JOIN olist_analytics.order_items AS i ON i.seller_id = s.seller_id
        LEFT JOIN olist_analytics.orders AS o ON o.order_id = i.order_id
        WHERE s.seller_id ILIKE %s OR s.seller_city ILIKE %s
        GROUP BY s.seller_id, s.seller_state, s.seller_city
        ORDER BY merchandise_revenue DESC
        LIMIT %s
        """,
        (f"%{search_term.strip()}%", f"%{search_term.strip()}%", limit),
    )


