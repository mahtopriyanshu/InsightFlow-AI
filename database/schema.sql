-- InsightFlow AI - Olist curated schema
-- Target: PostgreSQL 16+
-- Run order: schema.sql -> constraints.sql -> indexes.sql

BEGIN;

CREATE SCHEMA IF NOT EXISTS olist_analytics;
SET search_path TO olist_analytics, public;

-- 1. Conformed category lookup. ETL expands the supplied translation source
-- with approved untranslated/unknown members before dependent products load.
CREATE TABLE IF NOT EXISTS product_category_translation (
    product_category_name         text,
    product_category_name_english text,
    translation_status            text DEFAULT 'translated',
    etl_loaded_at                 timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- 2. One curated row per ZIP prefix. Raw geolocation observations are
-- deterministically consolidated before loading this table.
CREATE TABLE IF NOT EXISTS geolocation (
    geolocation_zip_code_prefix integer,
    geolocation_lat             numeric(10, 7),
    geolocation_lng             numeric(10, 7),
    geolocation_city            text,
    geolocation_state           char(2),
    observation_count           integer DEFAULT 0,
    coordinate_count            integer DEFAULT 0,
    geolocation_quality_status  text DEFAULT 'matched',
    etl_loaded_at               timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- 3. One source customer row per order-level customer identifier.
CREATE TABLE IF NOT EXISTS customers (
    customer_id              varchar(32),
    customer_unique_id       varchar(32),
    customer_zip_code_prefix integer,
    customer_city            text,
    customer_state           char(2),
    etl_loaded_at            timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- 4. One row per product.
CREATE TABLE IF NOT EXISTS products (
    product_id                 varchar(32),
    product_category_name      text,
    product_name_length        integer,
    product_description_length integer,
    product_photos_qty         integer,
    product_weight_g           integer,
    product_length_cm          integer,
    product_height_cm          integer,
    product_width_cm           integer,
    etl_loaded_at              timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- 5. One row per marketplace seller.
CREATE TABLE IF NOT EXISTS sellers (
    seller_id              varchar(32),
    seller_zip_code_prefix integer,
    seller_city            text,
    seller_state           char(2),
    etl_loaded_at          timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- 6. One row per order.
CREATE TABLE IF NOT EXISTS orders (
    order_id                       varchar(32),
    customer_id                    varchar(32),
    order_status                   text,
    order_purchase_timestamp       timestamp without time zone,
    order_approved_at              timestamp without time zone,
    order_delivered_carrier_date   timestamp without time zone,
    order_delivered_customer_date  timestamp without time zone,
    order_estimated_delivery_date  timestamp without time zone,
    etl_loaded_at                  timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- 7. One product/seller item sequence within an order.
CREATE TABLE IF NOT EXISTS order_items (
    order_id           varchar(32),
    order_item_id      integer,
    product_id         varchar(32),
    seller_id          varchar(32),
    shipping_limit_date timestamp without time zone,
    price              numeric(12, 2),
    freight_value      numeric(12, 2),
    etl_loaded_at      timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- 8. One sequential payment event within an order.
CREATE TABLE IF NOT EXISTS order_payments (
    order_id            varchar(32),
    payment_sequential  integer,
    payment_type        text,
    payment_installments integer,
    payment_value       numeric(12, 2),
    etl_loaded_at       timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- 9. One review/order pair. Neither source identifier is unique alone.
CREATE TABLE IF NOT EXISTS order_reviews (
    review_id                varchar(32),
    order_id                 varchar(32),
    review_score             smallint,
    review_comment_title     text,
    review_comment_message   text,
    review_creation_date     timestamp without time zone,
    review_answer_timestamp  timestamp without time zone,
    etl_loaded_at            timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

COMMIT;
