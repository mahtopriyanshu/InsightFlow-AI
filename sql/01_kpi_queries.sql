-- KPI 1: Count all marketplace orders.
SELECT COUNT(*) AS total_orders
FROM olist_analytics.orders;

-- KPI 2: Count distinct real customers using the stable customer identifier.
SELECT COUNT(DISTINCT customer_unique_id) AS total_customers
FROM olist_analytics.customers;

-- KPI 3: Calculate total collected revenue from all payment records.
SELECT ROUND(SUM(payment_value), 2) AS total_revenue
FROM olist_analytics.order_payments;

-- KPI 4: Calculate average collected revenue per paid order.
SELECT ROUND(
    SUM(payment_value) / NULLIF(COUNT(DISTINCT order_id), 0),
    2
) AS average_order_value
FROM olist_analytics.order_payments;

-- KPI 5: Calculate the percentage of orders successfully delivered.
SELECT ROUND(
    100.0 * SUM(CASE WHEN order_status = 'delivered' THEN 1 ELSE 0 END)
    / NULLIF(COUNT(*), 0),
    2
) AS delivered_order_rate_pct
FROM olist_analytics.orders;

-- KPI 6: Calculate the percentage of orders cancelled by customers or operations.
SELECT ROUND(
    100.0 * SUM(CASE WHEN order_status = 'canceled' THEN 1 ELSE 0 END)
    / NULLIF(COUNT(*), 0),
    2
) AS cancelled_order_rate_pct
FROM olist_analytics.orders;
