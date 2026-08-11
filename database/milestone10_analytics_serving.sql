-- Milestone 10: validated analytics-serving objects.
-- This migration changes schema objects only; it does not modify business rows.

SET lock_timeout = '5s';
SET statement_timeout = '120s';

CREATE MATERIALIZED VIEW IF NOT EXISTS olist_analytics.mv_order_revenue AS
WITH payment_totals AS (
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
)
SELECT
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_timestamp,
    COALESCE(p.payment_revenue, 0) AS payment_revenue,
    COALESCE(i.merchandise_value, 0) AS merchandise_value,
    COALESCE(i.freight_value, 0) AS freight_value,
    COALESCE(i.total_item_value, 0) AS total_item_value
FROM olist_analytics.orders AS o
LEFT JOIN payment_totals AS p ON p.order_id = o.order_id
LEFT JOIN item_totals AS i ON i.order_id = o.order_id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_order_revenue_order_id
    ON olist_analytics.mv_order_revenue (order_id);

CREATE OR REPLACE VIEW olist_analytics.vw_order_revenue AS
SELECT
    order_id, customer_id, order_status, order_purchase_timestamp,
    payment_revenue, merchandise_value, freight_value, total_item_value
FROM olist_analytics.mv_order_revenue;

CREATE OR REPLACE VIEW olist_analytics.vw_order_delivery_metrics AS
SELECT
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    CASE
        WHEN order_delivered_customer_date IS NULL THEN NULL
        ELSE EXTRACT(EPOCH FROM (
            order_delivered_customer_date - order_purchase_timestamp
        )) / 86400.0
    END AS actual_delivery_days,
    CASE
        WHEN order_delivered_customer_date IS NULL THEN NULL
        ELSE EXTRACT(EPOCH FROM (
            order_delivered_customer_date - order_estimated_delivery_date
        )) / 86400.0
    END AS delivery_delay_days,
    CASE
        WHEN order_delivered_customer_date IS NULL THEN 'not_delivered'
        WHEN order_delivered_customer_date > order_estimated_delivery_date
            THEN 'late'
        ELSE 'on_time_or_early'
    END AS delivery_performance
FROM olist_analytics.orders;

COMMENT ON MATERIALIZED VIEW olist_analytics.mv_order_revenue IS
    'One row per order; refresh after a successful curated ETL load.';
COMMENT ON VIEW olist_analytics.vw_order_revenue IS
    'Stable serving interface over the materialized per-order revenue fact.';
COMMENT ON VIEW olist_analytics.vw_order_delivery_metrics IS
    'Validated order delivery durations and promise-date classification.';

