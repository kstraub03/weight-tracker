import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection

# ----------------------------------------------------
# PAGE CONFIG & CUSTOM STYLES
# ----------------------------------------------------
st.set_page_config(page_title="Fitness Hub", page_icon="⚡", layout="centered")

st.markdown("""
<style>
    .hero-banner {
        background: linear-gradient(135deg, #e04848 0%, #f59e0b 100%);
        color: #ffffff;
        padding: 18px 22px;
        border-radius: 12px;
        margin-bottom: 14px;
        text-align: center;
    }
    .hero-day {
        font-size: 42px;
        font-weight: 800;
        line-height: 1.1;
        margin: 0;
    }
    .hero-sub {
        font-size: 14px;
        opacity: 0.92;
        margin-top: 4px;
    }
    .quote-card {
        background-color: #fff7ed;
        border-left: 4px solid #f59e0b;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 18px;
        font-size: 15px;
        font-style: italic;
        color: #374151;
    }
    .quote-author {
        display: block;
        margin-top: 6px;
        font-size: 12px;
        font-style: normal;
        color: #6b7280;
    }
    .rate-badge {
        padding: 8px 14px;
        border-radius: 6px;
        font-size: 14px;
        margin: 4px 0 12px 0;
        color: #1f2937;
    }
    .rate-green  { background-color: #dcfce7; border-left: 4px solid #16a34a; }
    .rate-yellow { background-color: #fef9c3; border-left: 4px solid #ca8a04; }
    .rate-orange { background-color: #ffedd5; border-left: 4px solid #ea580c; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# GSHEETS CONNECTION & DATA HELPERS
# ----------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet_name, default_cols):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=default_cols)
        df = df.dropna(how="all")
        for col in default_cols:
            if col not in
