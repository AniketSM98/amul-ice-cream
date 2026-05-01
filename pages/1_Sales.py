"""
pages/1_Sales.py — Record new sales & browse transaction history
"""

import streamlit as st
import pandas as pd
from config import CURRENCY
import db

st.set_page_config(page_title="Sales", page_icon="🧾", layout="wide")
st.title("🧾 Sales & Transactions")

tab_new, tab_history = st.tabs(["New Sale", "Transaction History"])

# ── NEW SALE ──────────────────────────────────────────────────────────────────
with tab_new:
    st.subheader("Record a New Sale")

    products_df = db.get_products(active_only=True)
    if products_df.empty:
        st.warning("No active products found. Add products first.")
        st.stop()

    product_names = products_df["name"].tolist()
    price_map = dict(zip(products_df["name"], products_df["price"]))
    id_map    = dict(zip(products_df["name"], products_df["product_id"]))

    # Order builder
    if "order_items" not in st.session_state:
        st.session_state.order_items = []

    col_form, col_cart = st.columns([1, 1])

    with col_form:
        st.markdown("**Add item to order**")
        selected_product = st.selectbox("Product", product_names, key="sel_product")
        qty = st.number_input("Quantity", min_value=1, max_value=20, value=1, key="sel_qty")

        if st.button("➕ Add to Order"):
            st.session_state.order_items.append({
                "product":    selected_product,
                "product_id": id_map[selected_product],
                "quantity":   qty,
                "unit_price": float(price_map[selected_product]),
                "subtotal":   round(qty * float(price_map[selected_product]), 2),
            })

        if st.button("🗑️ Clear Order"):
            st.session_state.order_items = []

    with col_cart:
        st.markdown("**Current Order**")
        if not st.session_state.order_items:
            st.info("No items added yet.")
        else:
            cart_df = pd.DataFrame(st.session_state.order_items)
            st.dataframe(
                cart_df[["product", "quantity", "unit_price", "subtotal"]].rename(
                    columns={"product": "Item", "quantity": "Qty",
                             "unit_price": "Price", "subtotal": "Subtotal"}
                ),
                use_container_width=True,
                hide_index=True,
            )
            total = cart_df["subtotal"].sum()
            st.markdown(f"### Total: **{CURRENCY}{total:.2f}**")

    if st.session_state.order_items:
        st.divider()
        col_pay, col_name, col_notes = st.columns(3)
        with col_pay:
            payment = st.selectbox("Payment Method", ["cash", "card", "upi", "other"])
        with col_name:
            customer = st.text_input("Customer Name (optional)")
        with col_notes:
            notes = st.text_input("Notes (optional)")

        if st.button("✅ Complete Sale", type="primary"):
            cart = st.session_state.order_items
            total = sum(i["subtotal"] for i in cart)

            txn_id = db.execute(
                """INSERT INTO transactions (total_amount, payment_method, customer_name, notes)
                   VALUES (%s, %s, %s, %s)""",
                (round(total, 2), payment, customer or None, notes or None),
            )

            db.executemany(
                """INSERT INTO transaction_items
                   (transaction_id, product_id, quantity, unit_price, subtotal)
                   VALUES (%s, %s, %s, %s, %s)""",
                [(txn_id, i["product_id"], i["quantity"], i["unit_price"], i["subtotal"])
                 for i in cart],
            )

            st.success(f"Sale #{txn_id} recorded! Total: {CURRENCY}{total:.2f}")
            st.session_state.order_items = []
            st.rerun()

# ── TRANSACTION HISTORY ───────────────────────────────────────────────────────
with tab_history:
    st.subheader("Transaction History")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        from datetime import date, timedelta
        date_from = st.date_input("From", value=date.today() - timedelta(days=7))
    with col_f2:
        date_to = st.date_input("To", value=date.today())
    with col_f3:
        method_filter = st.selectbox("Payment", ["All", "cash", "card", "upi", "other"])

    df = db.query_df("""
        SELECT transaction_id, transaction_date, total_amount,
               payment_method, customer_name
        FROM transactions
        WHERE DATE(transaction_date) BETWEEN %s AND %s
        ORDER BY transaction_date DESC
    """, (str(date_from), str(date_to)))

    if method_filter != "All":
        df = df[df["payment_method"] == method_filter]

    if df.empty:
        st.info("No transactions found for this period.")
    else:
        st.write(f"**{len(df)} transactions — Total: {CURRENCY}{df['total_amount'].sum():,.2f}**")
        st.dataframe(
            df.rename(columns={
                "transaction_id": "ID", "transaction_date": "Date/Time",
                "total_amount": "Amount", "payment_method": "Payment",
                "customer_name": "Customer",
            }),
            use_container_width=True,
            hide_index=True,
        )

        # Drill-down into a transaction
        st.divider()
        st.markdown("**View transaction details**")
        txn_ids = df["transaction_id"].tolist()
        sel_id = st.selectbox("Select Transaction ID", txn_ids)
        if sel_id:
            items_df = db.get_transaction_items(sel_id)
            st.dataframe(items_df, use_container_width=True, hide_index=True)
