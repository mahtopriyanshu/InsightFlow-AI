-- Sales 1: Show monthly order volume and payment revenue over time.
WITH order_revenue AS (
    SELECT
        order_id,
        SUM(payment_value) AS revenue
    FROM olist_analytics.order_payments
    GROUP BY order_id
)
SELECT
    date_trunc('month', o.order_purchase_timestamp)::date AS revenue_month,
    COUNT(*) AS orders,
    ROUND(SUM(COALESCE(r.revenue, 0)), 2) AS revenue
FROM olist_analytics.orders AS o
LEFT JOIN order_revenue AS r
    ON r.order_id = o.order_id
GROUP BY date_trunc('month', o.order_purchase_timestamp)
ORDER BY revenue_month;

-- Sales 2: Compare order counts and revenue by order status.
WITH order_revenue AS (
    SELECT
        order_id,
        SUM(payment_value) AS revenue
    FROM olist_analytics.order_payments
    GROUP BY order_id
)
SELECT
    o.order_status,
    COUNT(*) AS orders,
    ROUND(SUM(COALESCE(r.revenue, 0)), 2) AS revenue
FROM olist_analytics.orders AS o
LEFT JOIN order_revenue AS r
    ON r.order_id = o.order_id
GROUP BY o.order_status
ORDER BY revenue DESC;

-- Sales 3: Find the states generating the most collected revenue.
WITH order_revenue AS (
    SELECT
        order_id,
        SUM(payment_value) AS revenue
    FROM olist_analytics.order_payments
    GROUP BY order_id
)
SELECT
    c.customer_state,
    COUNT(o.order_id) AS orders,
    ROUND(SUM(COALESCE(r.revenue, 0)), 2) AS revenue
FROM olist_analytics.orders AS o
JOIN olist_analytics.customers AS c
    ON c.customer_id = o.customer_id
LEFT JOIN order_revenue AS r
    ON r.order_id = o.order_id
GROUP BY c.customer_state
ORDER BY revenue DESC, c.customer_state;

-- Sales 4: Compare merchandise value, freight, and total item value by month.
SELECT
    date_trunc('month', o.order_purchase_timestamp)::date AS sales_month,
    ROUND(SUM(oi.price), 2) AS merchandise_value,
    ROUND(SUM(oi.freight_value), 2) AS freight_value,
    ROUND(SUM(oi.price + oi.freight_value), 2) AS total_item_value
FROM olist_analytics.orders AS o
JOIN olist_analytics.order_items AS oi
    ON oi.order_id = o.order_id
GROUP BY date_trunc('month', o.order_purchase_timestamp)
ORDER BY sales_month;
