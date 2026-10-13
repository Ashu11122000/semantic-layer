
-- File: sql/01_raw/01_create_tables.sql
-- Purpose: Create raw tables for the seven e-commerce CSV datasets.
-- Run this after creating the raw schema.

CREATE TABLE IF NOT EXISTS raw.customers (
    customer_id     TEXT PRIMARY KEY,
    customer_name   TEXT,
    segment         TEXT,
    city            TEXT,
    region          TEXT,
    signup_date     DATE
);

CREATE TABLE IF NOT EXISTS raw.products (
    product_id      TEXT PRIMARY KEY,
    product_name    TEXT,
    category        TEXT,
    unit_price      NUMERIC(14, 2),
    unit_cost       NUMERIC(14, 2),
    active_flag     BOOLEAN
);

CREATE TABLE IF NOT EXISTS raw.orders (
    order_id        TEXT PRIMARY KEY,
    customer_id     TEXT,
    order_date      DATE,
    order_status    TEXT,
    shipping_fee    NUMERIC(14, 2),
    ship_date       DATE,
    delivery_date   DATE
);

CREATE TABLE IF NOT EXISTS raw.order_items (
    order_item_id       TEXT PRIMARY KEY,
    order_id            TEXT,
    product_id          TEXT,
    quantity            INTEGER,
    unit_price_at_sale  NUMERIC(14, 2),
    unit_cost_at_sale   NUMERIC(14, 2),
    discount_amount     NUMERIC(14, 2)
);

CREATE TABLE IF NOT EXISTS raw.payments (
    payment_id      TEXT PRIMARY KEY,
    order_id        TEXT,
    payment_method  TEXT,
    payment_status  TEXT,
    payment_date    DATE
);

CREATE TABLE IF NOT EXISTS raw.returns (
    return_id       TEXT PRIMARY KEY,
    order_id        TEXT,
    return_date     DATE,
    return_reason   TEXT
);

CREATE TABLE IF NOT EXISTS raw.reviews (
    review_id       TEXT PRIMARY KEY,
    order_id        TEXT,
    review_score    SMALLINT,
    review_date     DATE
);

COMMENT ON TABLE raw.customers IS
'Raw customer data imported from customers.csv.';

COMMENT ON TABLE raw.products IS
'Raw product catalogue imported from products.csv.';

COMMENT ON TABLE raw.orders IS
'Raw order and delivery data imported from orders.csv.';

COMMENT ON TABLE raw.order_items IS
'Raw order-line data imported from order_items.csv.';

COMMENT ON TABLE raw.payments IS
'Raw payment records imported from payments.csv.';

COMMENT ON TABLE raw.returns IS
'Raw return records imported from returns.csv.';

COMMENT ON TABLE raw.reviews IS
'Raw review records imported from reviews.csv.';
