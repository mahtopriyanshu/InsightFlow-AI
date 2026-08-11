-- Seller 1: Rank sellers by merchandise revenue and order volume.
SELECT
    s.seller_id,
    s.seller_state,
    COUNT(DISTINCT oi.order_id) AS orders,
    COUNT(*) AS items_sold,
    ROUND(SUM(oi.price), 2) AS merchandise_revenue
FROM olist_analytics.sellers AS s
JOIN olist_analytics.order_items AS oi
    ON oi.seller_id = s.seller_id
GROUP BY s.seller_id, s.seller_state
ORDER BY merchandise_revenue DESC
LIMIT 25;

-- Seller 2: Summarize seller count and merchandise revenue by state.
SELECT
    s.seller_state,
    COUNT(DISTINCT s.seller_id) AS sellers,
    COUNT(DISTINCT oi.order_id) AS orders,
    ROUND(SUM(oi.price), 2) AS merchandise_revenue
FROM olist_analytics.sellers AS s
LEFT JOIN olist_analytics.order_items AS oi
    ON oi.seller_id = s.seller_id
GROUP BY s.seller_state
ORDER BY merchandise_revenue DESC NULLS LAST;

-- Seller 3: Compare each seller's delivered and cancelled order counts.
SELECT
    s.seller_id,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    COUNT(DISTINCT CASE
        WHEN o.order_status = 'delivered' THEN oi.order_id
    END) AS delivered_orders,
    COUNT(DISTINCT CASE
        WHEN o.order_status = 'canceled' THEN oi.order_id
    END) AS cancelled_orders
FROM olist_analytics.sellers AS s
JOIN olist_analytics.order_items AS oi
    ON oi.seller_id = s.seller_id
JOIN olist_analytics.orders AS o
    ON o.order_id = oi.order_id
GROUP BY s.seller_id
ORDER BY delivered_orders DESC, total_orders DESC
LIMIT 25;

-- Seller 4: Identify sellers with the highest average item value.
SELECT
    s.seller_id,
    COUNT(*) AS items_sold,
    ROUND(AVG(oi.price), 2) AS average_item_value
FROM olist_analytics.sellers AS s
JOIN olist_analytics.order_items AS oi
    ON oi.seller_id = s.seller_id
GROUP BY s.seller_id
HAVING COUNT(*) >= 10
ORDER BY average_item_value DESC
LIMIT 25;
