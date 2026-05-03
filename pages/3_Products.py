"""
pages/3_Products.py — Manage the menu (products & categories)
"""

import streamlit as st
from config import CURRENCY
import db

st.set_page_config(page_title="Products", page_icon="🍨", layout="wide")
st.title("🍨 Products & Menu")

tab_view, tab_add, tab_edit, tab_categories = st.tabs(
    ["Menu Overview", "Add Product", "Edit Product", "Categories"]
)

# ── MENU OVERVIEW ─────────────────────────────────────────────────────────────
with tab_view:
    show_inactive = st.toggle("Show inactive products", value=False)
    df = db.get_products(active_only=not show_inactive)

    if df.empty:
        st.info("No products found.")
    else:
        for cat in df["category"].unique():
            st.markdown(f"#### {cat}")
            cat_df = df[df["category"] == cat][["name", "price", "is_active", "description"]]
            cat_df = cat_df.copy()
            cat_df["price"] = cat_df["price"].apply(lambda x: f"{CURRENCY}{x:.2f}")
            cat_df["is_active"] = cat_df["is_active"].apply(lambda x: "✅ Active" if x else "❌ Inactive")
            st.dataframe(
                cat_df.rename(columns={
                    "name": "Product", "price": "Price",
                    "is_active": "Status", "description": "Description",
                }),
                use_container_width=True,
                hide_index=True,
            )

# ── ADD PRODUCT ───────────────────────────────────────────────────────────────
with tab_add:
    st.subheader("Add New Product")

    categories_df = db.get_categories()
    cat_name_to_id = dict(zip(categories_df["name"], categories_df["category_id"]))

    name    = st.text_input("Product Name")
    cat     = st.selectbox("Category", categories_df["name"].tolist())
    price   = st.number_input(f"Price ({CURRENCY})", min_value=0.01, step=0.25, format="%.2f")
    desc    = st.text_area("Description (optional)")

    if st.button("Add Product", type="primary"):
        if not name.strip():
            st.warning("Please enter a product name.")
        else:
            try:
                db.execute(
                    """INSERT INTO products (name, category_id, price, description)
                       VALUES (%s, %s, %s, %s)""",
                    (name.strip(), cat_name_to_id[cat], price, desc.strip() or None),
                )
                st.success(f"'{name}' added to the menu!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ── EDIT PRODUCT ──────────────────────────────────────────────────────────────
with tab_edit:
    st.subheader("Edit Existing Product")

    df_all = db.get_products(active_only=False)
    product_names = df_all["name"].tolist()
    selected = st.selectbox("Select Product", product_names, key="edit_sel")
    row = df_all[df_all["name"] == selected].iloc[0]

    new_price  = st.number_input(
        f"Price ({CURRENCY})", value=float(row["price"]), step=0.25, format="%.2f"
    )
    new_desc   = st.text_area("Description", value=row["description"] or "")
    new_active = st.checkbox("Active (visible for sale)", value=bool(row["is_active"]))

    if st.button("Save Changes", type="primary"):
        db.execute(
            "UPDATE products SET price=%s, description=%s, is_active=%s WHERE product_id=%s",
            (new_price, new_desc.strip() or None, new_active, int(row["product_id"])),
        )
        st.success(f"'{selected}' updated!")
        st.rerun()

# ── CATEGORIES ────────────────────────────────────────────────────────────────
with tab_categories:
    st.subheader("Categories")
    cats = db.get_categories()
    st.dataframe(cats.rename(columns={"category_id": "ID", "name": "Category"}),
                 use_container_width=True, hide_index=True)

    st.divider()
    new_cat = st.text_input("New Category Name")
    if st.button("Add Category"):
        if not new_cat.strip():
            st.warning("Enter a category name.")
        else:
            try:
                db.execute("INSERT INTO categories (name) VALUES (%s)", (new_cat.strip(),))
                st.success(f"Category '{new_cat}' added!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
