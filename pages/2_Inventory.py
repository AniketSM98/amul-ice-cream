"""
pages/2_Inventory.py — Manage ingredient stock levels
"""

import streamlit as st
from config import CURRENCY
import db

st.set_page_config(page_title="Inventory", page_icon="📦", layout="wide")
st.title("📦 Inventory Management")

tab_view, tab_update, tab_add = st.tabs(["Stock Levels", "Update Stock", "Add Ingredient"])

# ── STOCK LEVELS ──────────────────────────────────────────────────────────────
with tab_view:
    df = db.get_inventory()

    # Color-code status
    status_colors = {"Out of Stock": "🔴", "Low": "🟡", "OK": "🟢"}
    df["Status"] = df["status"].map(status_colors) + " " + df["status"]

    col_ok   = df[df["status"] == "OK"]
    col_low  = df[df["status"] == "Low"]
    col_out  = df[df["status"] == "Out of Stock"]

    c1, c2, c3 = st.columns(3)
    c1.metric("OK",           len(col_ok),  delta=None)
    c2.metric("Low Stock",    len(col_low),  delta=None)
    c3.metric("Out of Stock", len(col_out), delta=None)

    st.divider()

    st.dataframe(
        df[["name", "quantity", "unit", "reorder_level", "cost_per_unit", "Status", "last_updated"]].rename(
            columns={
                "name": "Ingredient", "quantity": "Current Qty", "unit": "Unit",
                "reorder_level": "Reorder Level", "cost_per_unit": f"Cost/Unit ({CURRENCY})",
                "last_updated": "Last Updated",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

# ── UPDATE STOCK ──────────────────────────────────────────────────────────────
with tab_update:
    st.subheader("Adjust Stock Quantity")
    df_inv = db.get_inventory()

    ingredient = st.selectbox(
        "Ingredient",
        df_inv["name"].tolist(),
        key="upd_ingredient",
    )
    row = df_inv[df_inv["name"] == ingredient].iloc[0]

    st.write(f"Current quantity: **{row['quantity']} {row['unit']}**")

    action = st.radio("Action", ["Add stock (restock)", "Remove stock (usage/waste)"], horizontal=True)
    amount = st.number_input("Amount", min_value=0.0, step=0.5, format="%.2f")
    reason = st.text_input("Reason (optional)", placeholder="e.g., Weekly delivery, Spilled")

    if st.button("Update Stock", type="primary"):
        if amount <= 0:
            st.warning("Enter an amount greater than 0.")
        else:
            delta = amount if "Add" in action else -amount
            new_qty = max(0.0, row["quantity"] + delta)
            db.execute(
                "UPDATE ingredients SET quantity = %s WHERE ingredient_id = %s",
                (new_qty, int(row["ingredient_id"])),
            )
            direction = "Added" if delta > 0 else "Removed"
            st.success(f"{direction} {amount} {row['unit']} of {ingredient}. New qty: {new_qty}")
            st.rerun()

# ── ADD INGREDIENT ─────────────────────────────────────────────────────────────
with tab_add:
    st.subheader("Add New Ingredient")

    name         = st.text_input("Ingredient Name")
    c1, c2       = st.columns(2)
    quantity     = c1.number_input("Initial Quantity", min_value=0.0, step=0.5, format="%.2f")
    unit         = c2.selectbox("Unit", ["kg", "liters", "pcs", "grams", "ml", "boxes"])
    c3, c4       = st.columns(2)
    reorder_lvl  = c3.number_input("Reorder Level", min_value=0.0, step=0.5, format="%.2f")
    cost         = c4.number_input(f"Cost per Unit ({CURRENCY})", min_value=0.0, step=0.10, format="%.2f")

    if st.button("Add Ingredient", type="primary"):
        if not name.strip():
            st.warning("Please enter an ingredient name.")
        else:
            try:
                db.execute(
                    """INSERT INTO ingredients (name, quantity, unit, reorder_level, cost_per_unit)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (name.strip(), quantity, unit, reorder_lvl, cost),
                )
                st.success(f"'{name}' added to inventory!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
