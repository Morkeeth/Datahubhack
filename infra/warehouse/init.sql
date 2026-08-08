CREATE SCHEMA ecommerce;

CREATE TABLE ecommerce.customers (
    customer_id BIGINT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    country_code CHAR(2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ecommerce.products (
    product_id BIGINT PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0)
);

CREATE TABLE ecommerce.orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES ecommerce.customers(customer_id),
    status TEXT NOT NULL CHECK (status IN ('pending', 'paid', 'shipped')),
    ordered_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE ecommerce.order_items (
    order_id BIGINT NOT NULL REFERENCES ecommerce.orders(order_id),
    product_id BIGINT NOT NULL REFERENCES ecommerce.products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    PRIMARY KEY (order_id, product_id)
);

CREATE TABLE ecommerce.trials (
    trial_id BIGINT PRIMARY KEY,
    cohort_id TEXT NOT NULL,
    trial_started_at TIMESTAMPTZ NOT NULL,
    converted_at TIMESTAMPTZ
);

CREATE TABLE ecommerce.revenue_events (
    event_id BIGINT PRIMARY KEY,
    month TEXT NOT NULL,
    segment TEXT NOT NULL,
    mrr NUMERIC(14, 2) NOT NULL,
    churned_mrr NUMERIC(14, 2) NOT NULL DEFAULT 0
);

CREATE TABLE ecommerce.pipeline_performance (
    rep_id TEXT PRIMARY KEY,
    pipeline_value NUMERIC(14, 2) NOT NULL,
    quota NUMERIC(14, 2) NOT NULL,
    coverage_ratio NUMERIC(8, 3) NOT NULL
);

INSERT INTO ecommerce.customers (customer_id, email, country_code, created_at)
VALUES
    (101, 'ada@example.com', 'GB', '2026-08-01T09:00:00Z'),
    (102, 'grace@example.com', 'US', '2026-08-02T10:30:00Z'),
    (103, 'linus@example.com', 'FI', '2026-08-03T14:15:00Z');

INSERT INTO ecommerce.products (product_id, sku, name, unit_price)
VALUES
    (501, 'DATA-MUG', 'Data Quality Mug', 18.00),
    (502, 'GRAPH-TEE', 'Metadata Graph T-Shirt', 29.00),
    (503, 'LINEAGE-PIN', 'Lineage Enamel Pin', 9.50);

INSERT INTO ecommerce.orders (order_id, customer_id, status, ordered_at)
VALUES
    (1001, 101, 'paid', '2026-08-04T11:00:00Z'),
    (1002, 102, 'shipped', '2026-08-05T12:20:00Z'),
    (1003, 101, 'pending', '2026-08-06T16:45:00Z');

INSERT INTO ecommerce.order_items (order_id, product_id, quantity, unit_price)
VALUES
    (1001, 501, 1, 18.00),
    (1001, 503, 2, 9.50),
    (1002, 502, 1, 29.00),
    (1003, 503, 3, 9.50);

INSERT INTO ecommerce.trials (
    trial_id, cohort_id, trial_started_at, converted_at
)
VALUES
    (2001, '2026-q1', '2026-01-01T09:00:00Z', '2026-01-20T14:00:00Z'),
    (2002, '2026-q1', '2026-01-03T10:00:00Z', NULL),
    (2003, '2026-q2', '2026-04-02T12:00:00Z', '2026-04-10T08:30:00Z');

INSERT INTO ecommerce.revenue_events (event_id, month, segment, mrr, churned_mrr)
VALUES
    (3001, '2026-08', 'startup', 12500.00, 500.00),
    (3002, '2026-08', 'scaleup', 32000.00, 1200.00),
    (3003, '2026-08', 'enterprise', 68000.00, 2500.00);

INSERT INTO ecommerce.pipeline_performance (
    rep_id, pipeline_value, quota, coverage_ratio
)
VALUES
    ('rep-ada', 450000.00, 150000.00, 3.000),
    ('rep-grace', 280000.00, 125000.00, 2.240),
    ('rep-linus', 510000.00, 175000.00, 2.914);

CREATE VIEW ecommerce.customer_order_summary AS
SELECT
    c.customer_id,
    c.email,
    count(o.order_id) AS order_count,
    coalesce(sum(oi.quantity * oi.unit_price), 0) AS lifetime_value
FROM ecommerce.customers AS c
LEFT JOIN ecommerce.orders AS o USING (customer_id)
LEFT JOIN ecommerce.order_items AS oi USING (order_id)
GROUP BY c.customer_id, c.email;

COMMENT ON SCHEMA ecommerce IS
    'Seeded writable warehouse schema for local DataHub agent development.';
COMMENT ON TABLE ecommerce.customers IS
    'Customer accounts used by the local development substrate.';
COMMENT ON TABLE ecommerce.orders IS
    'Customer orders with enforced customer relationships.';
COMMENT ON TABLE ecommerce.trials IS
    'Disclosed demo trials used by the Nullspace dbt solidification flow.';
COMMENT ON TABLE ecommerce.revenue_events IS
    'Disclosed demo revenue events used by requester-derived ghost contracts.';
COMMENT ON TABLE ecommerce.pipeline_performance IS
    'Disclosed demo sales pipeline used by requester-driven builder decisions.';
