-- Ice Cream Shop Database Schema
CREATE DATABASE IF NOT EXISTS ice_cream_shop;
USE ice_cream_shop;

-- ─────────────────────────────────────────
-- CATEGORIES
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categories (
    category_id   INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(50) NOT NULL UNIQUE
);

-- ─────────────────────────────────────────
-- PRODUCTS (menu items)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    product_id    INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    category_id   INT NOT NULL,
    price         DECIMAL(10,2) NOT NULL,
    description   TEXT,
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- ─────────────────────────────────────────
-- INGREDIENTS / INVENTORY
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ingredients (
    ingredient_id  INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(100) NOT NULL UNIQUE,
    quantity       DECIMAL(10,2) NOT NULL DEFAULT 0,
    unit           VARCHAR(20)  NOT NULL,           -- e.g. kg, liters, pcs
    reorder_level  DECIMAL(10,2) NOT NULL DEFAULT 10,
    cost_per_unit  DECIMAL(10,2) DEFAULT 0,
    last_updated   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────
-- TRANSACTIONS (each customer sale)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id   INT AUTO_INCREMENT PRIMARY KEY,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount     DECIMAL(10,2) NOT NULL,
    payment_method   ENUM('cash', 'card', 'upi', 'other') DEFAULT 'cash',
    customer_name    VARCHAR(100),
    notes            TEXT
);

-- ─────────────────────────────────────────
-- TRANSACTION ITEMS (line items per sale)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transaction_items (
    item_id         INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id  INT NOT NULL,
    product_id      INT NOT NULL,
    quantity        INT NOT NULL DEFAULT 1,
    unit_price      DECIMAL(10,2) NOT NULL,
    subtotal        DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id)     REFERENCES products(product_id)
);

-- ─────────────────────────────────────────
-- USEFUL VIEWS
-- ─────────────────────────────────────────

-- Daily revenue summary
CREATE OR REPLACE VIEW vw_daily_revenue AS
SELECT
    DATE(transaction_date) AS sale_date,
    COUNT(*)               AS num_transactions,
    SUM(total_amount)      AS total_revenue,
    AVG(total_amount)      AS avg_order_value
FROM transactions
GROUP BY DATE(transaction_date);

-- Top selling products
CREATE OR REPLACE VIEW vw_top_products AS
SELECT
    p.product_id,
    p.name,
    c.name          AS category,
    SUM(ti.quantity)   AS total_qty_sold,
    SUM(ti.subtotal)   AS total_revenue
FROM transaction_items ti
JOIN products p  ON ti.product_id   = p.product_id
JOIN categories c ON p.category_id  = c.category_id
GROUP BY p.product_id, p.name, c.name;

-- Low stock alert view
CREATE OR REPLACE VIEW vw_low_stock AS
SELECT
    ingredient_id,
    name,
    quantity,
    unit,
    reorder_level,
    (quantity - reorder_level) AS stock_gap
FROM ingredients
WHERE quantity <= reorder_level;
