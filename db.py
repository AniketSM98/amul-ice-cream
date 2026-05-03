"""
db.py — MySQL connection helpers.
All query functions return pandas DataFrames or scalar values.
Works locally (via .env) and on Streamlit Cloud (via st.secrets + TiDB SSL).
"""

import pandas as pd
import mysql.connector
from mysql.connector import pooling
from config import get_db_config

# Lazy pool — created on first use so Streamlit secrets are loaded by then
_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="icecream", pool_size=5, **get_db_config()
        )
    return _pool


def _conn():
    return _get_pool().get_connection()


def query_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Run a SELECT and return a DataFrame."""
    conn = _conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        rows = cur.fetchall()
        if rows:
            return pd.DataFrame(rows)
        cols = [desc[0] for desc in cur.description] if cur.description else []
        return pd.DataFrame(columns=cols)
    finally:
        conn.close()


def execute(sql: str, params: tuple = ()) -> int:
    """Run INSERT/UPDATE/DELETE. Returns lastrowid."""
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def executemany(sql: str, data: list):
    """Bulk INSERT/UPDATE."""
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.executemany(sql, data)
        conn.commit()
    finally:
        conn.close()


# ── Convenience queries ───────────────────────────────────────────────────────

def get_products(active_only=False) -> pd.DataFrame:
    where = "WHERE p.is_active = TRUE" if active_only else ""
    return query_df(f"""
        SELECT p.product_id, p.name, c.name AS category,
               p.price, p.is_active, p.description
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        {where}
        ORDER BY c.name, p.name
    """)


def get_categories() -> pd.DataFrame:
    return query_df("SELECT category_id, name FROM categories ORDER BY name")


def get_inventory() -> pd.DataFrame:
    return query_df("""
        SELECT ingredient_id, name, quantity, unit,
               reorder_level, cost_per_unit, last_updated,
               CASE
                   WHEN quantity = 0             THEN 'Out of Stock'
                   WHEN quantity <= reorder_level THEN 'Low'
                   ELSE 'OK'
               END AS status
        FROM ingredients
        ORDER BY status, name
    """)


def get_low_stock() -> pd.DataFrame:
    return query_df("SELECT * FROM vw_low_stock ORDER BY stock_gap")


def get_recent_transactions(limit=50) -> pd.DataFrame:
    return query_df(f"""
        SELECT transaction_id, transaction_date, total_amount,
               payment_method, customer_name
        FROM transactions
        ORDER BY transaction_date DESC
        LIMIT {limit}
    """)


def get_transaction_items(transaction_id: int) -> pd.DataFrame:
    return query_df("""
        SELECT p.name AS product, ti.quantity, ti.unit_price, ti.subtotal
        FROM transaction_items ti
        JOIN products p ON ti.product_id = p.product_id
        WHERE ti.transaction_id = %s
    """, (transaction_id,))


def get_daily_revenue(days=30) -> pd.DataFrame:
    return query_df(f"""
        SELECT DATE(transaction_date) AS sale_date,
               COUNT(*)               AS num_transactions,
               SUM(total_amount)      AS total_revenue,
               AVG(total_amount)      AS avg_order_value
        FROM transactions
        WHERE transaction_date >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
        GROUP BY DATE(transaction_date)
        ORDER BY sale_date
    """)


def get_top_products(days=30, limit=10) -> pd.DataFrame:
    return query_df(f"""
        SELECT p.name, c.name AS category,
               SUM(ti.quantity)  AS total_qty,
               SUM(ti.subtotal)  AS total_revenue
        FROM transaction_items ti
        JOIN products p     ON ti.product_id  = p.product_id
        JOIN categories c   ON p.category_id  = c.category_id
        JOIN transactions t ON ti.transaction_id = t.transaction_id
        WHERE t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
        GROUP BY p.product_id, p.name, c.name
        ORDER BY total_revenue DESC
        LIMIT {limit}
    """)


def get_payment_breakdown(days=30) -> pd.DataFrame:
    return query_df(f"""
        SELECT payment_method,
               COUNT(*)          AS num_transactions,
               SUM(total_amount) AS total_revenue
        FROM transactions
        WHERE transaction_date >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
        GROUP BY payment_method
    """)


def get_today_kpis() -> dict:
    df = query_df("""
        SELECT
            COALESCE(SUM(total_amount), 0) AS revenue,
            COUNT(*) AS transactions
        FROM transactions
        WHERE DATE(transaction_date) = CURDATE()
    """)
    low = len(get_low_stock())
    return {
        "revenue":      float(df["revenue"].iloc[0]),
        "transactions": int(df["transactions"].iloc[0]),
        "low_stock":    low,
    }


def get_hourly_sales(days=30) -> pd.DataFrame:
    return query_df(f"""
        SELECT HOUR(transaction_date) AS hour,
               DAYNAME(transaction_date) AS day_name,
               COUNT(*) AS num_sales
        FROM transactions
        WHERE transaction_date >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
        GROUP BY hour, day_name
    """)
