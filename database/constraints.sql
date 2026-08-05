-- InsightFlow AI - Olist keys and validation constraints
-- Target: PostgreSQL 16+
-- Prerequisite: schema.sql has completed successfully.
-- This migration is intended to run once under a migration tool.

BEGIN;

SET search_path TO olist_analytics, public;

-- Primary keys and uniqueness
ALTER TABLE product_category_translation
    ADD CONSTRAINT pk_product_category_translation
    PRIMARY KEY (product_category_name);

ALTER TABLE geolocation
    ADD CONSTRAINT pk_geolocation
    PRIMARY KEY (geolocation_zip_code_prefix);

ALTER TABLE customers
    ADD CONSTRAINT pk_customers
    PRIMARY KEY (customer_id);

ALTER TABLE products
    ADD CONSTRAINT pk_products
    PRIMARY KEY (product_id);

ALTER TABLE sellers
    ADD CONSTRAINT pk_sellers
    PRIMARY KEY (seller_id);

ALTER TABLE orders
    ADD CONSTRAINT pk_orders
    PRIMARY KEY (order_id),
    ADD CONSTRAINT uq_orders_customer_id
    UNIQUE (customer_id);

ALTER TABLE order_items
    ADD CONSTRAINT pk_order_items
    PRIMARY KEY (order_id, order_item_id);

ALTER TABLE order_payments
    ADD CONSTRAINT pk_order_payments
    PRIMARY KEY (order_id, payment_sequential);

ALTER TABLE order_reviews
    ADD CONSTRAINT pk_order_reviews
    PRIMARY KEY (review_id, order_id);

-- Required fields
ALTER TABLE product_category_translation
    ALTER COLUMN product_category_name SET NOT NULL,
    ALTER COLUMN translation_status SET NOT NULL,
    ALTER COLUMN etl_loaded_at SET NOT NULL;

ALTER TABLE geolocation
    ALTER COLUMN geolocation_zip_code_prefix SET NOT NULL,
    ALTER COLUMN observation_count SET NOT NULL,
    ALTER COLUMN coordinate_count SET NOT NULL,
    ALTER COLUMN geolocation_quality_status SET NOT NULL,
    ALTER COLUMN etl_loaded_at SET NOT NULL;

ALTER TABLE customers
    ALTER COLUMN customer_id SET NOT NULL,
    ALTER COLUMN customer_unique_id SET NOT NULL,
    ALTER COLUMN customer_zip_code_prefix SET NOT NULL,
    ALTER COLUMN customer_city SET NOT NULL,
    ALTER COLUMN customer_state SET NOT NULL,
    ALTER COLUMN etl_loaded_at SET NOT NULL;

ALTER TABLE products
    ALTER COLUMN product_id SET NOT NULL,
    ALTER COLUMN product_category_name SET NOT NULL,
    ALTER COLUMN etl_loaded_at SET NOT NULL;

ALTER TABLE sellers
    ALTER COLUMN seller_id SET NOT NULL,
    ALTER COLUMN seller_zip_code_prefix SET NOT NULL,
    ALTER COLUMN seller_city SET NOT NULL,
    ALTER COLUMN seller_state SET NOT NULL,
    ALTER COLUMN etl_loaded_at SET NOT NULL;

ALTER TABLE orders
    ALTER COLUMN order_id SET NOT NULL,
    ALTER COLUMN customer_id SET NOT NULL,
    ALTER COLUMN order_status SET NOT NULL,
    ALTER COLUMN order_purchase_timestamp SET NOT NULL,
    ALTER COLUMN order_estimated_delivery_date SET NOT NULL,
    ALTER COLUMN etl_loaded_at SET NOT NULL;

ALTER TABLE order_items
    ALTER COLUMN order_id SET NOT NULL,
    ALTER COLUMN order_item_id SET NOT NULL,
    ALTER COLUMN product_id SET NOT NULL,
    ALTER COLUMN seller_id SET NOT NULL,
    ALTER COLUMN shipping_limit_date SET NOT NULL,
    ALTER COLUMN price SET NOT NULL,
    ALTER COLUMN freight_value SET NOT NULL,
    ALTER COLUMN etl_loaded_at SET NOT NULL;

ALTER TABLE order_payments
    ALTER COLUMN order_id SET NOT NULL,
    ALTER COLUMN payment_sequential SET NOT NULL,
    ALTER COLUMN payment_type SET NOT NULL,
    ALTER COLUMN payment_installments SET NOT NULL,
    ALTER COLUMN payment_value SET NOT NULL,
    ALTER COLUMN etl_loaded_at SET NOT NULL;

ALTER TABLE order_reviews
    ALTER COLUMN review_id SET NOT NULL,
    ALTER COLUMN order_id SET NOT NULL,
    ALTER COLUMN review_score SET NOT NULL,
    ALTER COLUMN review_creation_date SET NOT NULL,
    ALTER COLUMN review_answer_timestamp SET NOT NULL,
    ALTER COLUMN etl_loaded_at SET NOT NULL;

-- Domain and business checks
ALTER TABLE product_category_translation
    ADD CONSTRAINT ck_category_name_not_blank
        CHECK (btrim(product_category_name) <> ''),
    ADD CONSTRAINT ck_category_translation_status
        CHECK (translation_status IN ('translated', 'missing_translation', 'unknown')),
    ADD CONSTRAINT ck_category_english_by_status
        CHECK (
            (translation_status = 'translated' AND product_category_name_english IS NOT NULL)
            OR translation_status IN ('missing_translation', 'unknown')
        );

ALTER TABLE geolocation
    ADD CONSTRAINT ck_geolocation_zip_nonnegative
        CHECK (geolocation_zip_code_prefix >= 0),
    ADD CONSTRAINT ck_geolocation_latitude
        CHECK (geolocation_lat IS NULL OR geolocation_lat BETWEEN -90 AND 90),
    ADD CONSTRAINT ck_geolocation_longitude
        CHECK (geolocation_lng IS NULL OR geolocation_lng BETWEEN -180 AND 180),
    ADD CONSTRAINT ck_geolocation_state
        CHECK (geolocation_state IS NULL OR geolocation_state ~ '^[A-Z]{2}$'),
    ADD CONSTRAINT ck_geolocation_counts
        CHECK (observation_count >= 0 AND coordinate_count >= 0
               AND coordinate_count <= observation_count),
    ADD CONSTRAINT ck_geolocation_quality_status
        CHECK (geolocation_quality_status IN ('matched', 'ambiguous', 'unmatched', 'unknown')),
    ADD CONSTRAINT ck_geolocation_unknown_coordinates
        CHECK (
            geolocation_quality_status NOT IN ('unmatched', 'unknown')
            OR (geolocation_lat IS NULL AND geolocation_lng IS NULL)
        );

ALTER TABLE customers
    ADD CONSTRAINT ck_customers_id_length
        CHECK (length(customer_id) = 32 AND length(customer_unique_id) = 32),
    ADD CONSTRAINT ck_customers_zip_nonnegative
        CHECK (customer_zip_code_prefix >= 0),
    ADD CONSTRAINT ck_customers_city_not_blank
        CHECK (btrim(customer_city) <> ''),
    ADD CONSTRAINT ck_customers_state
        CHECK (customer_state ~ '^[A-Z]{2}$');

ALTER TABLE products
    ADD CONSTRAINT ck_products_id_length
        CHECK (length(product_id) = 32),
    ADD CONSTRAINT ck_products_name_length
        CHECK (product_name_length IS NULL OR product_name_length >= 0),
    ADD CONSTRAINT ck_products_description_length
        CHECK (product_description_length IS NULL OR product_description_length >= 0),
    ADD CONSTRAINT ck_products_photos
        CHECK (product_photos_qty IS NULL OR product_photos_qty >= 0),
    ADD CONSTRAINT ck_products_weight
        CHECK (product_weight_g IS NULL OR product_weight_g >= 0),
    ADD CONSTRAINT ck_products_dimensions
        CHECK (
            (product_length_cm IS NULL OR product_length_cm >= 0)
            AND (product_height_cm IS NULL OR product_height_cm >= 0)
            AND (product_width_cm IS NULL OR product_width_cm >= 0)
        );

ALTER TABLE sellers
    ADD CONSTRAINT ck_sellers_id_length
        CHECK (length(seller_id) = 32),
    ADD CONSTRAINT ck_sellers_zip_nonnegative
        CHECK (seller_zip_code_prefix >= 0),
    ADD CONSTRAINT ck_sellers_city_not_blank
        CHECK (btrim(seller_city) <> ''),
    ADD CONSTRAINT ck_sellers_state
        CHECK (seller_state ~ '^[A-Z]{2}$');

ALTER TABLE orders
    ADD CONSTRAINT ck_orders_id_length
        CHECK (length(order_id) = 32 AND length(customer_id) = 32),
    ADD CONSTRAINT ck_orders_status
        CHECK (order_status IN (
            'created', 'approved', 'invoiced', 'processing',
            'shipped', 'delivered', 'canceled', 'unavailable'
        )),
    ADD CONSTRAINT ck_orders_approval_chronology
        CHECK (order_approved_at IS NULL
               OR order_approved_at >= order_purchase_timestamp),
    ADD CONSTRAINT ck_orders_carrier_chronology
        CHECK (order_delivered_carrier_date IS NULL
               OR order_approved_at IS NULL
               OR order_delivered_carrier_date >= order_approved_at),
    ADD CONSTRAINT ck_orders_delivery_chronology
        CHECK (order_delivered_customer_date IS NULL
               OR order_delivered_carrier_date IS NULL
               OR order_delivered_customer_date >= order_delivered_carrier_date);

ALTER TABLE order_items
    ADD CONSTRAINT ck_order_items_id_lengths
        CHECK (length(order_id) = 32 AND length(product_id) = 32 AND length(seller_id) = 32),
    ADD CONSTRAINT ck_order_items_sequence
        CHECK (order_item_id > 0),
    ADD CONSTRAINT ck_order_items_price
        CHECK (price >= 0),
    ADD CONSTRAINT ck_order_items_freight
        CHECK (freight_value >= 0);

ALTER TABLE order_payments
    ADD CONSTRAINT ck_order_payments_id_length
        CHECK (length(order_id) = 32),
    ADD CONSTRAINT ck_order_payments_sequence
        CHECK (payment_sequential > 0),
    ADD CONSTRAINT ck_order_payments_type_not_blank
        CHECK (btrim(payment_type) <> ''),
    ADD CONSTRAINT ck_order_payments_installments
        CHECK (payment_installments >= 0),
    ADD CONSTRAINT ck_order_payments_value
        CHECK (payment_value >= 0);

ALTER TABLE order_reviews
    ADD CONSTRAINT ck_order_reviews_id_lengths
        CHECK (length(review_id) = 32 AND length(order_id) = 32),
    ADD CONSTRAINT ck_order_reviews_score
        CHECK (review_score BETWEEN 1 AND 5),
    ADD CONSTRAINT ck_order_reviews_chronology
        CHECK (review_answer_timestamp >= review_creation_date);

-- Foreign keys are added after all primary keys to make dependencies explicit.
ALTER TABLE customers
    ADD CONSTRAINT fk_customers_geolocation
    FOREIGN KEY (customer_zip_code_prefix)
    REFERENCES geolocation (geolocation_zip_code_prefix)
    ON UPDATE RESTRICT ON DELETE RESTRICT;

ALTER TABLE products
    ADD CONSTRAINT fk_products_category
    FOREIGN KEY (product_category_name)
    REFERENCES product_category_translation (product_category_name)
    ON UPDATE RESTRICT ON DELETE RESTRICT;

ALTER TABLE sellers
    ADD CONSTRAINT fk_sellers_geolocation
    FOREIGN KEY (seller_zip_code_prefix)
    REFERENCES geolocation (geolocation_zip_code_prefix)
    ON UPDATE RESTRICT ON DELETE RESTRICT;

ALTER TABLE orders
    ADD CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id)
    REFERENCES customers (customer_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT;

ALTER TABLE order_items
    ADD CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id) REFERENCES orders (order_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id) REFERENCES products (product_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT fk_order_items_seller
        FOREIGN KEY (seller_id) REFERENCES sellers (seller_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT;

ALTER TABLE order_payments
    ADD CONSTRAINT fk_order_payments_order
    FOREIGN KEY (order_id)
    REFERENCES orders (order_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT;

ALTER TABLE order_reviews
    ADD CONSTRAINT fk_order_reviews_order
    FOREIGN KEY (order_id)
    REFERENCES orders (order_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT;

COMMIT;
