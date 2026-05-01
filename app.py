"""
app.py — Home Dashboard
"""

import streamlit as st
import plotly.express as px
from config import SHOP_NAME, CURRENCY
import db

st.set_page_config(
    page_title=SHOP_NAME,
    page_icon="🍦",
    layout="wide",
)

st.title(f"🍦 {SHOP_NAME}")
st.subheader("Dashboard")

# ── Today's KPIs ─────────────────────────────────────────────────────────────
kpis = db.get_today_kpis()

col1, col2, col3 = st.columns(3)
col1.metric("Today's Revenue",      f"{CURRENCY}{kpis['revenue']:,.2f}")
col2.metric("Today's Transactions", kpis["transactions"])
col3.metric(
    "Low Stock Alerts",
    kpis["low_stock"],
    delta=None if kpis["low_stock"] == 0 else f"{kpis['low_stock']} items need reorder",
    delta_color="inverse",
)

st.divider()

# ── Revenue last 14 days ──────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Revenue — Last 14 Days")
    df_rev = db.get_daily_revenue(days=14)
    if df_rev.empty:
        st.info("No sales data yet.")
    else:
        fig = px.bar(
            df_rev,
            x="sale_date",
            y="total_revenue",
            labels={"sale_date": "Date", "total_revenue": f"Revenue ({CURRENCY})"},
            color_discrete_sequence=["#F9A825"],
        )
        fig.update_layout(showlegend=False, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Top 5 Products (30 days)")
    df_top = db.get_top_products(days=30, limit=5)
    if df_top.empty:
        st.info("No sales data yet.")
    else:
        fig2 = px.bar(
            df_top.sort_values("total_revenue"),
            x="total_revenue",
            y="name",
            orientation="h",
            labels={"total_revenue": f"Revenue ({CURRENCY})", "name": ""},
            color_discrete_sequence=["#EF5350"],
        )
        fig2.update_layout(showlegend=False, margin=dict(t=20, b=20))
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Low stock alerts ──────────────────────────────────────────────────────────
st.subheader("⚠️ Low Stock Alerts")
df_low = db.get_low_stock()
if df_low.empty:
    st.success("All ingredients are well stocked!")
else:
    st.dataframe(
        df_low[["name", "quantity", "unit", "reorder_level"]].rename(
            columns={"name": "Ingredient", "quantity": "Current Qty",
                     "unit": "Unit", "reorder_level": "Reorder Level"}
        ),
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# ── Recent Transactions ───────────────────────────────────────────────────────
st.subheader("Recent Transactions")
df_txn = db.get_recent_transactions(limit=10)
if df_txn.empty:
    st.info("No transactions yet.")
else:
    df_txn["total_amount"] = df_txn["total_amount"].apply(lambda x: f"{CURRENCY}{x:.2f}")
    st.dataframe(
        df_txn.rename(columns={
            "transaction_id": "ID", "transaction_date": "Date/Time",
            "total_amount": "Amount", "payment_method": "Payment",
            "customer_name": "Customer",
        }),
        use_container_width=True,
        hide_index=True,
    )
