-- Payment 1: Show payment method usage, value, and average payment amount.
SELECT
    payment_type,
    COUNT(*) AS payment_records,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(SUM(payment_value), 2) AS payment_value,
    ROUND(AVG(payment_value), 2) AS average_payment_value
FROM olist_analytics.order_payments
GROUP BY payment_type
ORDER BY payment_value DESC;

-- Payment 2: Calculate each payment method's share of total payment value.
WITH payment_totals AS (
    SELECT
        payment_type,
        SUM(payment_value) AS payment_value
    FROM olist_analytics.order_payments
    GROUP BY payment_type
),
grand_total AS (
    SELECT SUM(payment_value) AS payment_value
    FROM payment_totals
)
SELECT
    p.payment_type,
    ROUND(p.payment_value, 2) AS payment_value,
    ROUND(
        100.0 * p.payment_value / NULLIF(g.payment_value, 0),
        2
    ) AS payment_value_share_pct
FROM payment_totals AS p
CROSS JOIN grand_total AS g
ORDER BY p.payment_value DESC;

-- Payment 3: Analyze installment usage and average payment value.
SELECT
    payment_installments,
    COUNT(*) AS payment_records,
    ROUND(AVG(payment_value), 2) AS average_payment_value,
    ROUND(SUM(payment_value), 2) AS total_payment_value
FROM olist_analytics.order_payments
GROUP BY payment_installments
ORDER BY payment_installments;

-- Payment 4: Compare single-method and multi-method orders.
WITH methods_per_order AS (
    SELECT
        order_id,
        COUNT(DISTINCT payment_type) AS payment_methods,
        SUM(payment_value) AS order_payment_value
    FROM olist_analytics.order_payments
    GROUP BY order_id
)
SELECT
    CASE
        WHEN payment_methods = 1 THEN 'single_method'
        ELSE 'multiple_methods'
    END AS payment_pattern,
    COUNT(*) AS orders,
    ROUND(AVG(order_payment_value), 2) AS average_order_value
FROM methods_per_order
GROUP BY CASE
    WHEN payment_methods = 1 THEN 'single_method'
    ELSE 'multiple_methods'
END
ORDER BY orders DESC;
