-- Customer 1: Count unique customers by state.
SELECT
    customer_state,
    COUNT(DISTINCT customer_unique_id) AS unique_customers
FROM olist_analytics.customers
GROUP BY customer_state
ORDER BY unique_customers DESC, customer_state;

-- Customer 2: Identify repeat customers and their order counts.
SELECT
    c.customer_unique_id,
    COUNT(DISTINCT o.order_id) AS order_count
FROM olist_analytics.customers AS c
JOIN olist_analytics.orders AS o
    ON o.customer_id = c.customer_id
GROUP BY c.customer_unique_id
HAVING COUNT(DISTINCT o.order_id) > 1
ORDER BY order_count DESC, c.customer_unique_id;

-- Customer 3: Measure the share of unique customers who ordered more than once.
WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS order_count
    FROM olist_analytics.customers AS c
    JOIN olist_analytics.orders AS o
        ON o.customer_id = c.customer_id
    GROUP BY c.customer_unique_id
)
SELECT
    COUNT(*) AS customers_with_orders,
    SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    ROUND(
        100.0 * SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        2
    ) AS repeat_customer_rate_pct
FROM customer_orders;

-- Customer 4: Rank cities by unique customers and order volume.
SELECT
    c.customer_state,
    c.customer_city,
    COUNT(DISTINCT c.customer_unique_id) AS unique_customers,
    COUNT(o.order_id) AS orders
FROM olist_analytics.customers AS c
JOIN olist_analytics.orders AS o
    ON o.customer_id = c.customer_id
GROUP BY c.customer_state, c.customer_city
ORDER BY orders DESC, unique_customers DESC
LIMIT 25;
