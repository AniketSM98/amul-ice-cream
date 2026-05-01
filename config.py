import os
from dotenv import load_dotenv

load_dotenv()


def get_db_config() -> dict:
    """
    Returns DB connection config.
    On Streamlit Cloud  → reads from st.secrets
    On local machine    → reads from .env file
    """
    try:
        import streamlit as st
        s = st.secrets
        return {
            "host":         str(s["DB_HOST"]),
            "port":         int(s.get("DB_PORT", 4000)),
            "user":         str(s["DB_USER"]),
            "password":     str(s["DB_PASSWORD"]),
            "database":     str(s.get("DB_NAME", "ice_cream_shop")),
            "ssl_disabled": False,   # TiDB Cloud requires SSL
        }
    except Exception:
        return {
            "host":     os.getenv("DB_HOST", "localhost"),
            "port":     int(os.getenv("DB_PORT", "3306")),
            "user":     os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "ice_cream_shop"),
        }


# Keep a module-level reference for seed_data.py (uses .env only)
DB_CONFIG = get_db_config()

SHOP_NAME = "Scoops & Smiles Ice Cream"
CURRENCY = "$"
LOW_STOCK_THRESHOLD = 10  # units
