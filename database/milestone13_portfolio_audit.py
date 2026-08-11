"""Read-only grain, distribution, reconciliation, and threshold audit for M13."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit_app.database.connection import query_dataframe


def show(title, frame):
    print(f"\n## {title}\n{frame.to_string(index=False)}")


def main():
    show("Base grain", query_dataframe("""
      SELECT (SELECT COUNT(*) FROM olist_analytics.products) products,
             (SELECT COUNT(*) FROM olist_analytics.sellers) sellers,
             (SELECT COUNT(*) FROM olist_analytics.order_items) item_rows,
             (SELECT COUNT(DISTINCT order_id) FROM olist_analytics.order_items) item_orders,
             (SELECT COUNT(*) FROM olist_analytics.order_reviews) reviews,
             (SELECT COUNT(DISTINCT order_id) FROM olist_analytics.order_reviews) reviewed_orders
    """))
    show("Merchandise and freight source totals", query_dataframe("""
      SELECT SUM(price) merchandise_revenue, SUM(freight_value) freight,
             COUNT(*) units, COUNT(DISTINCT order_id) orders,
             COUNT(DISTINCT product_id) products, COUNT(DISTINCT seller_id) sellers
      FROM olist_analytics.order_items
    """))
    show("Category sample distributions", query_dataframe("""
      WITH items AS (
        SELECT COALESCE(t.product_category_name_english,p.product_category_name) category,
          COUNT(DISTINCT i.order_id) orders, COUNT(*) units, SUM(i.price) revenue
        FROM olist_analytics.order_items i JOIN olist_analytics.products p USING(product_id)
        LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name)
        GROUP BY 1), reviews AS (
        SELECT category, COUNT(*) reviews FROM (
          SELECT DISTINCT r.review_id,
            COALESCE(t.product_category_name_english,p.product_category_name) category
          FROM olist_analytics.order_reviews r JOIN olist_analytics.order_items i USING(order_id)
          JOIN olist_analytics.products p USING(product_id)
          LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name)) x GROUP BY 1)
      SELECT COUNT(*) groups,
        percentile_cont(.25) WITHIN GROUP(ORDER BY orders) q1_orders,
        percentile_cont(.5) WITHIN GROUP(ORDER BY orders) median_orders,
        percentile_cont(.75) WITHIN GROUP(ORDER BY orders) q3_orders,
        MAX(orders) max_orders,
        percentile_cont(.25) WITHIN GROUP(ORDER BY COALESCE(reviews,0)) q1_reviews,
        percentile_cont(.5) WITHIN GROUP(ORDER BY COALESCE(reviews,0)) median_reviews,
        percentile_cont(.75) WITHIN GROUP(ORDER BY COALESCE(reviews,0)) q3_reviews,
        MAX(COALESCE(reviews,0)) max_reviews
      FROM items LEFT JOIN reviews USING(category)
    """))
    show("Product sample distributions", query_dataframe("""
      WITH x AS (SELECT product_id, COUNT(DISTINCT order_id) orders, COUNT(*) units,
                        SUM(price) revenue FROM olist_analytics.order_items GROUP BY product_id)
      SELECT COUNT(*) products,
        percentile_cont(.5) WITHIN GROUP(ORDER BY orders) median_orders,
        percentile_cont(.75) WITHIN GROUP(ORDER BY orders) q3_orders,
        percentile_cont(.9) WITHIN GROUP(ORDER BY orders) p90_orders,
        percentile_cont(.95) WITHIN GROUP(ORDER BY orders) p95_orders,
        MAX(orders) max_orders FROM x
    """))
    show("Seller sample distributions", query_dataframe("""
      WITH x AS (SELECT seller_id, COUNT(DISTINCT order_id) orders, COUNT(*) units,
                        SUM(price) revenue FROM olist_analytics.order_items GROUP BY seller_id)
      SELECT COUNT(*) sellers,
        percentile_cont(.25) WITHIN GROUP(ORDER BY orders) q1_orders,
        percentile_cont(.5) WITHIN GROUP(ORDER BY orders) median_orders,
        percentile_cont(.75) WITHIN GROUP(ORDER BY orders) q3_orders,
        percentile_cont(.9) WITHIN GROUP(ORDER BY orders) p90_orders,
        percentile_cont(.95) WITHIN GROUP(ORDER BY orders) p95_orders,
        MAX(orders) max_orders FROM x
    """))
    show("Orders spanning entities", query_dataframe("""
      WITH x AS (SELECT order_id, COUNT(DISTINCT seller_id) sellers,
                 COUNT(DISTINCT product_id) products FROM olist_analytics.order_items GROUP BY order_id)
      SELECT COUNT(*) orders, SUM((sellers>1)::int) multi_seller_orders,
             MAX(sellers) max_sellers, SUM((products>1)::int) multi_product_orders,
             MAX(products) max_products FROM x
    """))


if __name__ == "__main__": main()
