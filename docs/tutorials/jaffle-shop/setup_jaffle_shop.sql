-- Build the jaffle shop database used by the bitol-skills tutorials.
--
-- Run from this directory (docs/tutorials/jaffle-shop/):
--
--   duckdb jaffle_shop.duckdb < setup_jaffle_shop.sql
--
-- or, without the DuckDB CLI:
--
--   uv run --with duckdb python -c "import duckdb, pathlib; \
--       duckdb.connect('jaffle_shop.duckdb').sql(pathlib.Path('setup_jaffle_shop.sql').read_text())"
--
-- It loads the three seed CSVs as raw tables (into the default `main` schema
-- of jaffle_shop.duckdb) and derives the two marts
-- (orders, customers) that the tutorials write data contracts for. The
-- transformations mirror dbt-labs' classic jaffle_shop project.

-- --- Raw layer: the seeds, loaded as-is -------------------------------------

CREATE OR REPLACE TABLE raw_customers AS
SELECT
    id::INTEGER      AS id,
    first_name::VARCHAR AS first_name,
    last_name::VARCHAR  AS last_name
FROM read_csv('seeds/raw_customers.csv', header = true);

CREATE OR REPLACE TABLE raw_orders AS
SELECT
    id::INTEGER      AS id,
    user_id::INTEGER AS user_id,
    order_date::DATE AS order_date,
    status::VARCHAR  AS status
FROM read_csv('seeds/raw_orders.csv', header = true);

CREATE OR REPLACE TABLE raw_payments AS
SELECT
    id::INTEGER             AS id,
    order_id::INTEGER       AS order_id,
    payment_method::VARCHAR AS payment_method,
    amount::INTEGER         AS amount        -- integer cents
FROM read_csv('seeds/raw_payments.csv', header = true);

-- --- Mart layer: what the data product promises to consumers ----------------

-- One row per order, with the payment total pivoted out per method and
-- converted from cents to a currency amount.
CREATE OR REPLACE TABLE orders AS
WITH order_payments AS (
    SELECT
        order_id,
        SUM(CASE WHEN payment_method = 'credit_card'   THEN amount ELSE 0 END) AS credit_card_amount,
        SUM(CASE WHEN payment_method = 'coupon'        THEN amount ELSE 0 END) AS coupon_amount,
        SUM(CASE WHEN payment_method = 'bank_transfer' THEN amount ELSE 0 END) AS bank_transfer_amount,
        SUM(CASE WHEN payment_method = 'gift_card'     THEN amount ELSE 0 END) AS gift_card_amount,
        SUM(amount)                                                            AS total_amount
    FROM raw_payments
    GROUP BY order_id
)
SELECT
    o.id                                                        AS order_id,
    o.user_id                                                   AS customer_id,
    o.order_date                                                AS order_date,
    o.status                                                    AS status,
    CAST(COALESCE(p.credit_card_amount, 0)   / 100.0 AS DECIMAL(10, 2)) AS credit_card_amount,
    CAST(COALESCE(p.coupon_amount, 0)        / 100.0 AS DECIMAL(10, 2)) AS coupon_amount,
    CAST(COALESCE(p.bank_transfer_amount, 0) / 100.0 AS DECIMAL(10, 2)) AS bank_transfer_amount,
    CAST(COALESCE(p.gift_card_amount, 0)     / 100.0 AS DECIMAL(10, 2)) AS gift_card_amount,
    CAST(COALESCE(p.total_amount, 0)         / 100.0 AS DECIMAL(10, 2)) AS amount
FROM raw_orders AS o
LEFT JOIN order_payments AS p ON o.id = p.order_id;

-- One row per customer, with order history rolled up.
CREATE OR REPLACE TABLE customers AS
SELECT
    c.id                                                  AS customer_id,
    c.first_name                                          AS first_name,
    c.last_name                                           AS last_name,
    MIN(o.order_date)                                     AS first_order,
    MAX(o.order_date)                                     AS most_recent_order,
    COUNT(o.order_id)::INTEGER                            AS number_of_orders,
    CAST(COALESCE(SUM(o.amount), 0) AS DECIMAL(10, 2))    AS customer_lifetime_value
FROM raw_customers AS c
LEFT JOIN orders AS o ON c.id = o.customer_id
GROUP BY ALL;
