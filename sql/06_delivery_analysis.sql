-- Delivery 1: Calculate average delivery time for completed deliveries.
SELECT ROUND(
    AVG(EXTRACT(EPOCH FROM (
        order_delivered_customer_date - order_purchase_timestamp
    )) / 86400.0),
    2
) AS average_delivery_days
FROM olist_analytics.orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL;

-- Delivery 2: Calculate the share of delivered orders that arrived late.
SELECT
    COUNT(*) AS delivered_orders,
    SUM(CASE
        WHEN order_delivered_customer_date > order_estimated_delivery_date
        THEN 1 ELSE 0
    END) AS late_orders,
    ROUND(
        100.0 * SUM(CASE
            WHEN order_delivered_customer_date > order_estimated_delivery_date
            THEN 1 ELSE 0
        END) / NULLIF(COUNT(*), 0),
        2
    ) AS late_delivery_rate_pct
FROM olist_analytics.orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL;

-- Delivery 3: Compare delivery speed and late-delivery rate by customer state.
SELECT
    c.customer_state,
    COUNT(*) AS delivered_orders,
    ROUND(AVG(EXTRACT(EPOCH FROM (
        o.order_delivered_customer_date - o.order_purchase_timestamp
    )) / 86400.0), 2) AS average_delivery_days,
    ROUND(
        100.0 * SUM(CASE
            WHEN o.order_delivered_customer_date
                 > o.order_estimated_delivery_date
            THEN 1 ELSE 0
        END) / NULLIF(COUNT(*), 0),
        2
    ) AS late_delivery_rate_pct
FROM olist_analytics.orders AS o
JOIN olist_analytics.customers AS c
    ON c.customer_id = o.customer_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY late_delivery_rate_pct DESC, delivered_orders DESC;

-- Delivery 4: Show the monthly trend in promised-versus-actual delivery.
SELECT
    date_trunc('month', order_purchase_timestamp)::date AS order_month,
    COUNT(*) AS delivered_orders,
    ROUND(AVG(EXTRACT(EPOCH FROM (
        order_delivered_customer_date - order_estimated_delivery_date
    )) / 86400.0), 2) AS average_days_after_estimate
FROM olist_analytics.orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
GROUP BY date_trunc('month', order_purchase_timestamp)
ORDER BY order_month;
