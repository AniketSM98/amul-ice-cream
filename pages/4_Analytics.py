"""
pages/4_Analytics.py — Sales analytics & reports
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from config import CURRENCY
import db

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")
st.title("📊 Analytics & Reports")

# ── Date range selector ───────────────────────────────────────────────────────
col_r1, col_r2 = st.columns([1, 3])
with col_r1:
    days = st.selectbox("Period", [7, 14, 30, 60, 90], index=2, format_func=lambda x: f"Last {x} days")

# ── KPI row ───────────────────────────────────────────────────────────────────
df_rev   = db.get_daily_revenue(days=days)
df_top   = db.get_top_products(days=days, limit=10)
df_pay   = db.get_payment_breakdown(days=days)

total_rev   = df_rev["total_revenue"].sum()     if not df_rev.empty else 0
total_txns  = df_rev["num_transactions"].sum()  if not df_rev.empty else 0
avg_order   = (total_rev / total_txns)          if total_txns > 0 else 0
best_seller = df_top["name"].iloc[0]            if not df_top.empty else "—"

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Revenue ({days}d)",      f"{CURRENCY}{total_rev:,.2f}")
c2.metric(f"Transactions ({days}d)", f"{int(total_txns):,}")
c3.metric("Avg Order Value",         f"{CURRENCY}{avg_order:.2f}")
c4.metric("Best Seller",             best_seller)

st.divider()

# ── Revenue trend ─────────────────────────────────────────────────────────────
st.subheader("Revenue Trend")
if df_rev.empty:
    st.info("No data available.")
else:
    fig = px.line(
        df_rev,
        x="sale_date",
        y="total_revenue",
        markers=True,
        labels={"sale_date": "Date", "total_revenue": f"Revenue ({CURRENCY})"},
        color_discrete_sequence=["#1E88E5"],
    )
    fig.add_bar(
        x=df_rev["sale_date"],
        y=df_rev["total_revenue"],
        name="Revenue",
        marker_color="rgba(30,136,229,0.25)",
        showlegend=False,
    )
    fig.update_layout(margin=dict(t=10, b=20))
    st.plotly_chart(fig, use_container_width=True)

# ── Top products & Payment breakdown ──────────────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("Top Products by Revenue")
    if df_top.empty:
        st.info("No data.")
    else:
        fig2 = px.bar(
            df_top.sort_values("total_revenue"),
            x="total_revenue",
            y="name",
            orientation="h",
            color="category",
            labels={"total_revenue": f"Revenue ({CURRENCY})", "name": "", "category": "Category"},
        )
        fig2.update_layout(margin=dict(t=10, b=20))
        st.plotly_chart(fig2, use_container_width=True)

with col_r:
    st.subheader("Payment Methods")
    if df_pay.empty:
        st.info("No data.")
    else:
        fig3 = px.pie(
            df_pay,
            names="payment_method",
            values="total_revenue",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig3.update_traces(textposition="inside", textinfo="percent+label")
        fig3.update_layout(showlegend=True, margin=dict(t=10, b=20))
        st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── Sales heatmap: day × hour ──────────────────────────────────────────────────
st.subheader("Sales Heatmap — Day of Week vs Hour")
df_hourly = db.get_hourly_sales(days=days)

if df_hourly.empty:
    st.info("No data.")
else:
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = (
        df_hourly
        .pivot_table(index="day_name", columns="hour", values="num_sales", fill_value=0)
        .reindex([d for d in day_order if d in df_hourly["day_name"].unique()])
    )
    fig4 = px.imshow(
        pivot,
        labels={"x": "Hour of Day", "y": "Day", "color": "# Sales"},
        color_continuous_scale="YlOrRd",
        aspect="auto",
    )
    fig4.update_layout(margin=dict(t=10, b=20))
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ── Category revenue breakdown ──────────────────────────────────────────────
st.subheader("Revenue by Category")
df_cat = db.query_df(f"""
    SELECT c.name AS category, SUM(ti.subtotal) AS revenue
    FROM transaction_items ti
    JOIN products p     ON ti.product_id    = p.product_id
    JOIN categories c   ON p.category_id   = c.category_id
    JOIN transactions t ON ti.transaction_id = t.transaction_id
    WHERE t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
    GROUP BY c.name
    ORDER BY revenue DESC
""")

if df_cat.empty:
    st.info("No data.")
else:
    fig5 = px.bar(
        df_cat,
        x="category",
        y="revenue",
        color="category",
        labels={"category": "Category", "revenue": f"Revenue ({CURRENCY})"},
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig5.update_layout(showlegend=False, margin=dict(t=10, b=20))
    st.plotly_chart(fig5, use_container_width=True)

# ── Raw data export ──────────────────────────────────────────────────────────
st.divider()
st.subheader("Export Data")
if not df_rev.empty:
    csv = df_rev.to_csv(index=False).encode()
    st.download_button(
        "Download Daily Revenue CSV",
        data=csv,
        file_name=f"revenue_last_{days}_days.csv",
        mime="text/csv",
    )
