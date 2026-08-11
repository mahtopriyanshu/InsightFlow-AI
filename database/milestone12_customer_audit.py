"""Read-only live-data audit used to choose the Milestone 12 RFM method."""
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit_app.database.connection import query_dataframe


def show(title: str, frame: pd.DataFrame) -> None:
    print(f"\n## {title}")
    print(frame.to_string(index=False))


def main() -> None:
    show("Customer identity grain", query_dataframe("""
        WITH mapping AS (
            SELECT customer_unique_id, COUNT(DISTINCT customer_id) customer_ids,
                   COUNT(DISTINCT customer_state) states,
                   COUNT(DISTINCT customer_city) cities
            FROM olist_analytics.customers GROUP BY customer_unique_id
        )
        SELECT COUNT(*) unique_customers,
               SUM((customer_ids > 1)::int) multi_customer_id_customers,
               MAX(customer_ids) max_customer_ids,
               SUM((states > 1)::int) multi_state_customers,
               SUM((cities > 1)::int) multi_city_customers
        FROM mapping
    """))
    show("Order status and revenue", query_dataframe("""
        SELECT o.order_status, COUNT(*) orders,
               SUM(COALESCE(v.payment_revenue, 0)) revenue
        FROM olist_analytics.orders o
        LEFT JOIN olist_analytics.vw_order_revenue v USING (order_id)
        GROUP BY o.order_status ORDER BY orders DESC
    """))

    rfm = query_dataframe("""
        SELECT c.customer_unique_id,
               MAX(o.order_purchase_timestamp)::date last_purchase,
               COUNT(DISTINCT o.order_id) frequency,
               SUM(COALESCE(v.payment_revenue, 0)) monetary
        FROM olist_analytics.customers c
        JOIN olist_analytics.orders o USING (customer_id)
        LEFT JOIN olist_analytics.vw_order_revenue v USING (order_id)
        GROUP BY c.customer_unique_id
    """)
    reference_date = pd.to_datetime(rfm["last_purchase"]).max() + pd.Timedelta(days=1)
    rfm["monetary"] = pd.to_numeric(rfm["monetary"], errors="coerce").fillna(0.0)
    rfm["recency"] = (reference_date - pd.to_datetime(rfm["last_purchase"])).dt.days
    stats = rfm[["recency", "frequency", "monetary"]].describe(
        percentiles=[.25, .5, .75]
    ).T.reset_index(names="metric")
    show("RFM distributions", stats)
    show("Frequency ties", rfm["frequency"].value_counts().sort_index().head(15)
         .rename_axis("frequency").reset_index(name="customers"))
    show("Revenue reconciliation", pd.DataFrame([{
        "rfm_customers": len(rfm),
        "rfm_revenue": float(rfm["monetary"].sum()),
        "zero_or_negative_monetary": int((rfm["monetary"] <= 0).sum()),
        "reference_date": reference_date.date(),
    }]))
    show("Repeat depth", query_dataframe("""
        WITH customer_orders AS (
          SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) orders,
                 MIN(o.order_purchase_timestamp)::date first_date,
                 MAX(o.order_purchase_timestamp)::date last_date
          FROM olist_analytics.customers c JOIN olist_analytics.orders o USING(customer_id)
          GROUP BY c.customer_unique_id
        )
        SELECT COUNT(*) customers,
               SUM((orders > 1)::int) repeat_customers,
               ROUND(100.0 * SUM((orders > 1)::int) / COUNT(*), 4) repeat_rate,
               SUM((last_date > first_date)::int) repeat_on_later_day,
               AVG((last_date - first_date)) FILTER (WHERE orders > 1) avg_repeat_span_days
        FROM customer_orders
    """))
    show("Cohort repeat activity", query_dataframe("""
        WITH purchases AS (
          SELECT c.customer_unique_id,
                 date_trunc('month', o.order_purchase_timestamp)::date order_month,
                 MIN(date_trunc('month', o.order_purchase_timestamp)::date)
                   OVER (PARTITION BY c.customer_unique_id) cohort_month
          FROM olist_analytics.customers c JOIN olist_analytics.orders o USING(customer_id)
        ), activity AS (
          SELECT customer_unique_id, cohort_month, order_month,
                 ((EXTRACT(YEAR FROM order_month)-EXTRACT(YEAR FROM cohort_month))*12
                  + EXTRACT(MONTH FROM order_month)-EXTRACT(MONTH FROM cohort_month))::int age
          FROM purchases GROUP BY 1,2,3
        )
        SELECT age, COUNT(DISTINCT customer_unique_id) active_customers
        FROM activity GROUP BY age ORDER BY age LIMIT 13
    """))


if __name__ == "__main__":
    main()
