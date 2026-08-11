-- Product 1: Find the highest-revenue product categories by item price.
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name)
        AS product_category,
    COUNT(DISTINCT p.product_id) AS products,
    COUNT(*) AS items_sold,
    ROUND(SUM(oi.price), 2) AS merchandise_revenue
FROM olist_analytics.order_items AS oi
JOIN olist_analytics.products AS p
    ON p.product_id = oi.product_id
LEFT JOIN olist_analytics.product_category_translation AS t
    ON t.product_category_name = p.product_category_name
GROUP BY COALESCE(t.product_category_name_english, p.product_category_name)
ORDER BY merchandise_revenue DESC
LIMIT 20;

-- Product 2: Find the most frequently purchased product categories.
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name)
        AS product_category,
    COUNT(*) AS items_sold,
    COUNT(DISTINCT oi.order_id) AS orders
FROM olist_analytics.order_items AS oi
JOIN olist_analytics.products AS p
    ON p.product_id = oi.product_id
LEFT JOIN olist_analytics.product_category_translation AS t
    ON t.product_category_name = p.product_category_name
GROUP BY COALESCE(t.product_category_name_english, p.product_category_name)
ORDER BY items_sold DESC
LIMIT 20;

-- Product 3: Compare average product dimensions and weight by category.
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name)
        AS product_category,
    COUNT(*) AS product_count,
    ROUND(AVG(p.product_weight_g), 2) AS average_weight_g,
    ROUND(AVG(p.product_length_cm), 2) AS average_length_cm,
    ROUND(AVG(p.product_height_cm), 2) AS average_height_cm,
    ROUND(AVG(p.product_width_cm), 2) AS average_width_cm
FROM olist_analytics.products AS p
LEFT JOIN olist_analytics.product_category_translation AS t
    ON t.product_category_name = p.product_category_name
GROUP BY COALESCE(t.product_category_name_english, p.product_category_name)
ORDER BY product_count DESC;

-- Product 4: Show category revenue split between delivered and other orders.
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name)
        AS product_category,
    ROUND(SUM(
        CASE WHEN o.order_status = 'delivered' THEN oi.price ELSE 0 END
    ), 2) AS delivered_revenue,
    ROUND(SUM(
        CASE WHEN o.order_status <> 'delivered' THEN oi.price ELSE 0 END
    ), 2) AS other_status_revenue
FROM olist_analytics.order_items AS oi
JOIN olist_analytics.orders AS o
    ON o.order_id = oi.order_id
JOIN olist_analytics.products AS p
    ON p.product_id = oi.product_id
LEFT JOIN olist_analytics.product_category_translation AS t
    ON t.product_category_name = p.product_category_name
GROUP BY COALESCE(t.product_category_name_english, p.product_category_name)
ORDER BY delivered_revenue DESC;
