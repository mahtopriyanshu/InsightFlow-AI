-- InsightFlow AI - Olist query indexes
-- Target: PostgreSQL 16+
-- Prerequisite: schema.sql and constraints.sql have completed.
-- PostgreSQL automatically indexes PRIMARY KEY and UNIQUE constraints;
-- those indexes are not duplicated here.

BEGIN;

SET search_path TO olist_analytics, public;

-- Customer identity, geography, and regional filtering
CREATE INDEX IF NOT EXISTS idx_customers_unique_id
    ON customers (customer_unique_id);

CREATE INDEX IF NOT EXISTS idx_customers_state
    ON customers (customer_state);

CREATE INDEX IF NOT EXISTS idx_customers_zip_code_prefix
    ON customers (customer_zip_code_prefix);

-- Geography and category label filtering
CREATE INDEX IF NOT EXISTS idx_geolocation_state
    ON geolocation (geolocation_state);

CREATE INDEX IF NOT EXISTS idx_category_english
    ON product_category_translation (product_category_name_english);

CREATE INDEX IF NOT EXISTS idx_products_category
    ON products (product_category_name);

-- Seller location filtering and geography FK joins
CREATE INDEX IF NOT EXISTS idx_sellers_state
    ON sellers (seller_state);

CREATE INDEX IF NOT EXISTS idx_sellers_zip_code_prefix
    ON sellers (seller_zip_code_prefix);

-- Time-series reporting and common status-with-time filtering
CREATE INDEX IF NOT EXISTS idx_orders_purchase_timestamp
    ON orders (order_purchase_timestamp);

CREATE INDEX IF NOT EXISTS idx_orders_status_purchase_timestamp
    ON orders (order_status, order_purchase_timestamp);

-- Product, seller, and shipping-deadline item analysis
CREATE INDEX IF NOT EXISTS idx_order_items_product_id
    ON order_items (product_id);

CREATE INDEX IF NOT EXISTS idx_order_items_seller_id
    ON order_items (seller_id);

CREATE INDEX IF NOT EXISTS idx_order_items_shipping_limit_date
    ON order_items (shipping_limit_date);

-- Payment-method analysis
CREATE INDEX IF NOT EXISTS idx_order_payments_type
    ON order_payments (payment_type);

-- Review/order joins, score filtering, and review trends
CREATE INDEX IF NOT EXISTS idx_order_reviews_order_id
    ON order_reviews (order_id);

CREATE INDEX IF NOT EXISTS idx_order_reviews_score
    ON order_reviews (review_score);

CREATE INDEX IF NOT EXISTS idx_order_reviews_creation_date
    ON order_reviews (review_creation_date);

COMMIT;
