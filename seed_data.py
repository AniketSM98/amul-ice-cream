"""
seed_data.py — Populates the ice_cream_shop DB with realistic sample data.
Run once after schema.sql:  python seed_data.py
"""

import random
from datetime import datetime, timedelta
import mysql.connector
from config import DB_CONFIG

conn = mysql.connector.connect(**DB_CONFIG)
cur = conn.cursor()

# ── Categories ──────────────────────────────────────────────────────────────
categories = ["Scoops", "Sundaes", "Milkshakes", "Cones", "Toppings"]
cur.executemany(
    "INSERT IGNORE INTO categories (name) VALUES (%s)",
    [(c,) for c in categories],
)

cur.execute("SELECT name, category_id FROM categories")
cat_map = {row[0]: row[1] for row in cur.fetchall()}

# ── Products ─────────────────────────────────────────────────────────────────
products = [
    # Scoops
    ("Vanilla Classic",     "Scoops",     3.50, "Single scoop of creamy vanilla"),
    ("Chocolate Fudge",     "Scoops",     3.50, "Rich Belgian chocolate"),
    ("Strawberry Bliss",    "Scoops",     3.50, "Fresh strawberry flavor"),
    ("Mint Choco Chip",     "Scoops",     4.00, "Cool mint with chocolate chips"),
    ("Butter Pecan",        "Scoops",     4.00, "Buttery roasted pecans"),
    ("Cookies & Cream",     "Scoops",     4.00, "Oreo crumbles in vanilla"),
    ("Mango Tango",         "Scoops",     4.50, "Tropical mango sorbet"),
    ("Salted Caramel",      "Scoops",     4.50, "House-made caramel swirl"),
    # Sundaes
    ("Classic Sundae",      "Sundaes",    6.99, "2 scoops + hot fudge + whipped cream"),
    ("Banana Split",        "Sundaes",    8.99, "Banana, 3 scoops, 3 toppings"),
    ("Brownie Blast",       "Sundaes",    7.99, "Warm brownie + vanilla scoop"),
    # Milkshakes
    ("Vanilla Shake",       "Milkshakes", 5.99, "Thick vanilla milkshake"),
    ("Chocolate Shake",     "Milkshakes", 5.99, "Rich chocolate milkshake"),
    ("Strawberry Shake",    "Milkshakes", 5.99, "Strawberry milkshake"),
    ("Oreo Shake",          "Milkshakes", 6.99, "Blended with Oreo cookies"),
    # Cones
    ("Waffle Cone",         "Cones",      1.00, "House-made waffle cone"),
    ("Sugar Cone",          "Cones",      0.50, "Classic sugar cone"),
    ("Chocolate Dipped",    "Cones",      1.50, "Waffle cone dipped in chocolate"),
    # Toppings
    ("Hot Fudge",           "Toppings",   0.75, "Warm chocolate fudge"),
    ("Caramel Drizzle",     "Toppings",   0.75, "Sweet caramel sauce"),
    ("Sprinkles",           "Toppings",   0.50, "Rainbow sprinkles"),
    ("Whipped Cream",       "Toppings",   0.50, "Fresh whipped cream"),
    ("Cherries",            "Toppings",   0.50, "Maraschino cherries"),
]

cur.executemany(
    "INSERT IGNORE INTO products (name, category_id, price, description) VALUES (%s,%s,%s,%s)",
    [(name, cat_map[cat], price, desc) for name, cat, price, desc in products],
)

cur.execute("SELECT product_id, price FROM products")
product_rows = cur.fetchall()  # [(id, price), ...]

# ── Ingredients / Inventory ──────────────────────────────────────────────────
ingredients = [
    ("Whole Milk",          120.0, "liters",  20.0,  0.80),
    ("Heavy Cream",          80.0, "liters",  15.0,  1.50),
    ("Sugar",                50.0, "kg",       8.0,  0.60),
    ("Vanilla Extract",       5.0, "liters",   1.0,  8.00),
    ("Cocoa Powder",         15.0, "kg",        3.0,  4.00),
    ("Strawberries",         20.0, "kg",        5.0,  3.50),
    ("Waffle Cones",        200.0, "pcs",      30.0,  0.30),
    ("Sugar Cones",         300.0, "pcs",      30.0,  0.15),
    ("Chocolate Chips",      12.0, "kg",        2.0,  5.00),
    ("Oreo Cookies",         10.0, "kg",        2.0,  6.00),
    ("Caramel Sauce",        15.0, "liters",    3.0,  4.50),
    ("Fudge Sauce",          12.0, "liters",    3.0,  4.00),
    ("Whipped Cream Cans",   25.0, "pcs",       5.0,  2.50),
    ("Maraschino Cherries",   4.0, "kg",        1.0,  7.00),
    ("Sprinkles",             3.0, "kg",        0.5,  3.00),
    ("Pecans",                8.0, "kg",        2.0, 12.00),
    ("Bananas",              15.0, "kg",        3.0,  1.20),
    ("Brownie Mix",          10.0, "kg",        2.0,  3.50),
    ("Mango Pulp",           18.0, "kg",        4.0,  3.00),
    ("Butter",                8.0, "kg",        1.5,  4.50),
]

cur.executemany(
    """INSERT IGNORE INTO ingredients (name, quantity, unit, reorder_level, cost_per_unit)
       VALUES (%s, %s, %s, %s, %s)""",
    ingredients,
)

# ── Transactions (last 45 days) ───────────────────────────────────────────────
payment_methods = ["cash", "card", "upi", "other"]
payment_weights = [0.35, 0.40, 0.20, 0.05]

scoop_ids    = [r[0] for r in product_rows[:8]]
sundae_ids   = [r[0] for r in product_rows[8:11]]
shake_ids    = [r[0] for r in product_rows[11:15]]
cone_ids     = [r[0] for r in product_rows[15:18]]
topping_ids  = [r[0] for r in product_rows[18:]]
price_map    = {r[0]: float(r[1]) for r in product_rows}

random.seed(42)
now = datetime.now()

for day_offset in range(45, 0, -1):
    sale_date = now - timedelta(days=day_offset)
    # More sales on weekends
    is_weekend = sale_date.weekday() >= 5
    num_transactions = random.randint(25, 50) if is_weekend else random.randint(10, 30)

    for _ in range(num_transactions):
        hour   = random.choices(range(10, 22), weights=[1,2,3,4,5,6,6,5,4,3,2,1])[0]
        minute = random.randint(0, 59)
        ts     = sale_date.replace(hour=hour, minute=minute, second=random.randint(0, 59))

        method = random.choices(payment_methods, weights=payment_weights)[0]

        # Build order: 1-2 scoops, maybe a cone, maybe toppings, or a shake/sundae
        order_type = random.choices(
            ["scoop", "sundae", "shake"], weights=[0.55, 0.25, 0.20]
        )[0]

        items = []
        if order_type == "scoop":
            num_scoops = random.randint(1, 3)
            for _ in range(num_scoops):
                pid = random.choice(scoop_ids)
                items.append((pid, 1, price_map[pid]))
            if random.random() < 0.70:
                cone_id = random.choice(cone_ids)
                items.append((cone_id, 1, price_map[cone_id]))
            for t_id in random.sample(topping_ids, k=random.randint(0, 2)):
                items.append((t_id, 1, price_map[t_id]))
        elif order_type == "sundae":
            pid = random.choice(sundae_ids)
            items.append((pid, 1, price_map[pid]))
            for t_id in random.sample(topping_ids, k=random.randint(0, 2)):
                items.append((t_id, 1, price_map[t_id]))
        else:
            pid = random.choice(shake_ids)
            qty = random.randint(1, 2)
            items.append((pid, qty, price_map[pid]))

        total = sum(qty * price for _, qty, price in items)

        cur.execute(
            """INSERT INTO transactions (transaction_date, total_amount, payment_method)
               VALUES (%s, %s, %s)""",
            (ts, round(total, 2), method),
        )
        txn_id = cur.lastrowid

        cur.executemany(
            """INSERT INTO transaction_items (transaction_id, product_id, quantity, unit_price, subtotal)
               VALUES (%s, %s, %s, %s, %s)""",
            [(txn_id, pid, qty, price, round(qty * price, 2)) for pid, qty, price in items],
        )

conn.commit()
cur.close()
conn.close()
print("✓ Seed data inserted successfully!")
