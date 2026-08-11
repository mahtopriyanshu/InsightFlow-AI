-- Review 1: Show the distribution of customer review scores.
SELECT
    review_score,
    COUNT(*) AS reviews,
    ROUND(
        100.0 * COUNT(*) / NULLIF(
            (SELECT COUNT(*) FROM olist_analytics.order_reviews),
            0
        ),
        2
    ) AS review_share_pct
FROM olist_analytics.order_reviews
GROUP BY review_score
ORDER BY review_score;

-- Review 2: Calculate the overall average review score.
SELECT ROUND(AVG(review_score), 2) AS average_review_score
FROM olist_analytics.order_reviews;

-- Review 3: Compare review scores for on-time and late deliveries.
SELECT
    CASE
        WHEN o.order_delivered_customer_date
             > o.order_estimated_delivery_date
        THEN 'late'
        ELSE 'on_time_or_early'
    END AS delivery_performance,
    COUNT(*) AS reviews,
    ROUND(AVG(r.review_score), 2) AS average_review_score
FROM olist_analytics.order_reviews AS r
JOIN olist_analytics.orders AS o
    ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY CASE
    WHEN o.order_delivered_customer_date
         > o.order_estimated_delivery_date
    THEN 'late'
    ELSE 'on_time_or_early'
END
ORDER BY average_review_score DESC;

-- Review 4: Find product categories with the strongest review scores.
WITH category_order_reviews AS (
    SELECT DISTINCT
        r.review_id,
        r.order_id,
        r.review_score,
        COALESCE(t.product_category_name_english, p.product_category_name)
            AS product_category
    FROM olist_analytics.order_reviews AS r
    JOIN olist_analytics.order_items AS oi
        ON oi.order_id = r.order_id
    JOIN olist_analytics.products AS p
        ON p.product_id = oi.product_id
    LEFT JOIN olist_analytics.product_category_translation AS t
        ON t.product_category_name = p.product_category_name
)
SELECT
    product_category,
    COUNT(*) AS reviewed_orders,
    ROUND(AVG(review_score), 2) AS average_review_score
FROM category_order_reviews
GROUP BY product_category
HAVING COUNT(*) >= 100
ORDER BY average_review_score DESC, reviewed_orders DESC;
