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
            if col not in df.columns:
                df[col] = None
        return df
    except Exception:
        return pd.DataFrame(columns=default_cols)

df_weights = load_data("weights", ["date", "weight"])

# ----------------------------------------------------
# TRANSFORMATION DAY COUNTER & QUOTE OF THE DAY
# ----------------------------------------------------
# Optional: set a fixed start date, e.g. date(2026, 9, 1).
# Leave as None to use the date of your first logged weight.
TRANSFORMATION_START = None

# Your target weight (kg)
GOAL_WEIGHT = 85.0

MOTIVATIONAL_QUOTES = [
    ("We are what we repeatedly do. Excellence, then, is not an act, but a habit.", "Will Durant (on Aristotle)"),
    ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
    ("Difficulties strengthen the mind, as labor does the body.", "Seneca"),
    ("Well done is better than well said.", "Benjamin Franklin"),
    ("The journey of a thousand miles begins with one step.", "Lao Tzu"),
    ("He who conquers himself is the mightiest warrior.", "Confucius"),
    ("No man has the right to be an amateur in the matter of physical training.", "Socrates"),
    ("Discipline is choosing between what you want now and what you want most.", "Unknown"),
    ("Small progress is still progress.", "Unknown"),
    ("The body achieves what the mind believes.", "Unknown"),
    ("Consistency beats intensity. Show up again tomorrow.", "Unknown"),
    ("You don't have to be extreme, just consistent.", "Unknown"),
    ("Every rep counts. Every meal counts. Every day counts.", "Unknown"),
    ("Strength doesn't come from what you can do. It comes from overcoming what you once couldn't.", "Unknown"),
    ("Trust the process. The scale is a trend, not a verdict.", "Unknown"),
]

# Quote library lives in the "quotes" worksheet (columns: quote, author).
# If that sheet is empty or missing, the built-in list above is used.
df_quotes = load_data("quotes", ["quote", "author"])
df_quotes = df_quotes[df_quotes["quote"].astype(str).str.strip().replace("nan", "") != ""].reset_index(drop=True)

def get_quote_pool():
    if not df_quotes.empty:
        return [(str(r["quote"]).strip(), str(r["author"]).strip() if pd.notna(r["author"]) and str(r["author"]).strip() else "Unknown")
                for _, r in df_quotes.iterrows()]
    return MOTIVATIONAL_QUOTES

def save_quotes(df):
    try:
        conn.update(worksheet="quotes", data=df)
    except Exception:
        conn.create(worksheet="quotes", data=df)

def get_daily_quote(today):
    # Same quote all day, a new one each day
    pool = get_quote_pool()
    return pool[today.toordinal() % len(pool)]

start_date = TRANSFORMATION_START
if start_date is None and not df_weights.empty:
    try:
        start_date = pd.to_datetime(df_weights["date"]).min().date()
    except Exception:
        start_date = None

if start_date is not None:
    day_number = (date.today() - start_date).days + 1
    weeks, rem_days = divmod(day_number - 1, 7)
    sub_text = f"Started {start_date.strftime('%d %b %Y')} &middot; {weeks} weeks, {rem_days} days in"

    # Total change since the first weigh-in
    try:
        df_tmp = df_weights.copy()
        df_tmp["date"] = pd.to_datetime(df_tmp["date"])
        df_tmp["weight"] = pd.to_numeric(df_tmp["weight"])
        df_tmp = df_tmp.sort_values("date")
        total_change = df_tmp.iloc[-1]["weight"] - df_tmp.iloc[0]["weight"]
        sub_text += f" &middot; {total_change:+.1f} kg total"
    except Exception:
        pass

    st.markdown(
        f"""<div class="hero-banner">
            <div class="hero-sub">TRANSFORMATION</div>
            <p class="hero-day">Day {day_number}</p>
            <div class="hero-sub">{sub_text}</div>
        </div>""",
        unsafe_allow_html=True
    )
else:
    st.info("Log your first weight to start your transformation day counter 💪")

quote_text, quote_author = get_daily_quote(date.today())
st.markdown(
    f"""<div class="quote-card">“{quote_text}”
        <span class="quote-author">— {quote_author}</span>
    </div>""",
    unsafe_allow_html=True
)

# ====================================================
# WEIGHT TRACKER
# ====================================================
st.title("⚖️ Daily Weight Tracker")

with st.form("weight_form", clear_on_submit=False):
    col_d, col_w = st.columns(2)
    with col_d:
        w_date = st.date_input("Date", date.today(), key="original_w_date")
    with col_w:
        w_val = st.number_input("Morning Weight (kg)", min_value=40.0, max_value=150.0, value=80.0, step=0.1, format="%.1f")
    submit_weight = st.form_submit_button("Record Weight", width="stretch")

    if submit_weight:
        date_str = w_date.strftime("%Y-%m-%d")
        df_weights_clean = df_weights[df_weights["date"] != date_str].copy()
        new_entry = pd.DataFrame([{"date": date_str, "weight": float(w_val)}])
        updated_weights = pd.concat([df_weights_clean, new_entry], ignore_index=True)
        conn.update(worksheet="weights", data=updated_weights)
        st.success(f"Recorded {w_val} kg for {date_str}!")
        st.rerun()

if not df_weights.empty:
    df_calc = df_weights.copy()
    df_calc["date"] = pd.to_datetime(df_calc["date"])
    df_calc["weight"] = pd.to_numeric(df_calc["weight"])
    df_calc = df_calc.sort_values("date").reset_index(drop=True)

    latest_wt = df_calc.iloc[-1]["weight"]

    # Kalenderwochen aufbereiten
    df_calc["KW"] = df_calc["date"].dt.isocalendar().week
    df_calc["Year"] = df_calc["date"].dt.isocalendar().year

    # Wöchentliche Durchschnitte aggregieren
    kw_grouped = df_calc.groupby(["Year", "KW"])["weight"].mean().reset_index().sort_values(["Year", "KW"])
    current_weekly_avg = kw_grouped.iloc[-1]["weight"]

    # 4-Wochen Durchschnitts-Vergleich
    if len(kw_grouped) >= 5:
        baseline_kw_avg = kw_grouped.iloc[-5]["weight"]
        monthly_diff_kg = current_weekly_avg - baseline_kw_avg
        monthly_diff_pct = (monthly_diff_kg / baseline_kw_avg) * 100
    elif len(kw_grouped) > 1:
        baseline_kw_avg = kw_grouped.iloc[0]["weight"]
        monthly_diff_kg = current_weekly_avg - baseline_kw_avg
        monthly_diff_pct = (monthly_diff_kg / baseline_kw_avg) * 100
    else:
        monthly_diff_kg = 0.0
        monthly_diff_pct = 0.0

    st.markdown("---")

    # TOGGLE: % vs. absolute (kg)
    gain_format = st.radio("Monthly Gain Display", ["Absolute (kg)", "Percentage (%)"], horizontal=True)

    # METRICS: Current Weight (links) | Weekly Average mit "i" (mitte) | Monthly Gain mit "i" (rechts)
    m1, m2, m3 = st.columns(3)
    m1.metric("Current Weight", f"{latest_wt:.1f} kg")
    m2.metric(
        "Weekly Average", 
        f"{current_weekly_avg:.2f} kg",
        help="Average morning weight for the current calendar week. Filters out daily water and sodium fluctuations."
    )
    if gain_format == "Absolute (kg)":
        m3.metric(
            "Monthly Gain", 
            f"{monthly_diff_kg:+.2f} kg",
            help="Calculated as (Current KW Avg - KW Avg 4 Weeks Prior). Target: 1.0% - 2.0% body weight gain per month for a lean bulk."
        )
    else:
        m3.metric(
            "Monthly Gain", 
            f"{monthly_diff_pct:+.2f} %",
            help="Calculated as ((Current KW Avg - KW Avg 4 Weeks Prior) / KW Avg 4 Weeks Prior) * 100. Target: 1.0% - 2.0% body weight gain per month for a lean bulk."
        )

    # RATE CHECK (lean bulk target: 1.0% - 2.0% per month)
    if len(kw_grouped) > 1:
        if monthly_diff_pct < 1.0:
            rate_cls, rate_msg = "rate-yellow", f"🐢 {monthly_diff_pct:+.2f}% / month: below the 1–2% target. Consider eating a bit more."
        elif monthly_diff_pct <= 2.0:
            rate_cls, rate_msg = "rate-green", f"✅ {monthly_diff_pct:+.2f}% / month: right in the 1–2% lean bulk sweet spot."
        else:
            rate_cls, rate_msg = "rate-orange", f"🚀 {monthly_diff_pct:+.2f}% / month: above the 2% target. Gaining faster than a lean bulk."
        st.markdown(f'<div class="rate-badge {rate_cls}">{rate_msg}</div>', unsafe_allow_html=True)
    else:
        st.caption("Rate check appears once you have at least two calendar weeks of data.")

    # GOAL PROGRESS
    st.markdown("---")
    st.subheader(f"🎯 Goal: {GOAL_WEIGHT:.1f} kg")
    start_wt = df_calc.iloc[0]["weight"]
    remaining = GOAL_WEIGHT - current_weekly_avg
    if GOAL_WEIGHT != start_wt:
        progress = (current_weekly_avg - start_wt) / (GOAL_WEIGHT - start_wt)
    else:
        progress = 1.0
    progress = float(min(max(progress, 0.0), 1.0))
    st.progress(progress, text=f"{progress*100:.0f}% of the way: {start_wt:.1f} kg → {current_weekly_avg:.1f} kg (weekly avg) → {GOAL_WEIGHT:.1f} kg")

    if remaining <= 0:
        st.success("🏆 Goal reached! Time to set a new one.")
    else:
        # Trend over the last 28 days (linear fit, kg per day)
        recent = df_calc[df_calc["date"] >= df_calc["date"].max() - pd.Timedelta(days=28)]
        if len(recent) >= 5 and recent["date"].nunique() >= 5:
            x_days = (recent["date"] - recent["date"].min()).dt.days.to_numpy(dtype=float)
            slope = np.polyfit(x_days, recent["weight"].to_numpy(dtype=float), 1)[0]
            if slope > 0:
                eta = date.today() + timedelta(days=int(remaining / slope))
                st.caption(f"{remaining:.1f} kg to go. At your current pace ({slope*7:+.2f} kg/week) you'll hit {GOAL_WEIGHT:.0f} kg around **{eta.strftime('%d %b %Y')}**.")
            else:
                st.caption(f"{remaining:.1f} kg to go. Your last 4 weeks are flat or trending down, so no arrival date yet.")
        else:
            st.caption(f"{remaining:.1f} kg to go. A projected date appears after ~5 weigh-ins.")

    st.markdown("---")
    st.subheader("Weight Progression Chart")

    # TOGGLE: Daily vs. Calendar Weeks
    chart_view = st.radio("Chart Resolution", ["Daily", "Calendar Weeks (KW Average)"], horizontal=True)

    # Auto-scaling y-axis with a little padding
    y_min = float(np.floor(df_calc["weight"].min() - 0.5))
    y_max = float(np.ceil(df_calc["weight"].max() + 0.5))
    y_scale = alt.Scale(domain=[y_min, y_max])

    if chart_view == "Daily":
        df_calc["rolling_7"] = df_calc.set_index("date")["weight"].rolling("7D").mean().values
        base = alt.Chart(df_calc).encode(x=alt.X("date:T", title="Date", axis=alt.Axis(format="%d %b")))
        daily_line = base.mark_line(point=True, color="#e04848", opacity=0.55).encode(
            y=alt.Y("weight:Q", scale=y_scale, title="Weight (kg)"),
            tooltip=[alt.Tooltip("date:T", format="%Y-%m-%d"),
                     alt.Tooltip("weight:Q", format=".2f", title="Weight"),
                     alt.Tooltip("rolling_7:Q", format=".2f", title="7-day avg")]
        )
        rolling_line = base.mark_line(color="#1f2937", strokeWidth=2.5, strokeDash=[6, 3]).encode(
            y=alt.Y("rolling_7:Q", scale=y_scale)
        )
        chart = (daily_line + rolling_line).properties(height=320)
        st.caption("Red: daily weigh-ins · Dashed: 7-day rolling average")
    else:
        kw_trend = df_calc.groupby(["Year", "KW"]).agg(
            weight=("weight", "mean"),
            date=("date", "min")
        ).reset_index().sort_values(["Year", "KW"])
        kw_trend["KW_Label"] = kw_trend.apply(lambda r: f"KW {int(r['KW'])}", axis=1)

        chart = alt.Chart(kw_trend).mark_line(point=True, color="#e04848").encode(
            x=alt.X("KW_Label:N", title="Calendar Week", sort=None),
            y=alt.Y("weight:Q", scale=y_scale, title="Average Weight (kg)"),
            tooltip=["KW_Label:N", alt.Tooltip("weight:Q", format=".2f", title="Ø Weight")]
        ).properties(height=320)

    st.altair_chart(chart, width="stretch")

    # KALENDERWOCHEN TABELLE
    st.subheader("Calendar Week (KW) Summary")
    kw_summary = df_calc.groupby(["Year", "KW"])["weight"].agg(
        Average="mean",
        Min="min",
        Max="max",
        Entries="count"
    ).reset_index().sort_values(["Year", "KW"], ascending=False)
    kw_summary["Average"] = kw_summary["Average"].round(2)
    kw_summary["Range"] = kw_summary.apply(lambda r: f"{r['Min']:.1f} - {r['Max']:.1f} kg", axis=1)

    # Transformation week number (Week 1 = calendar week of your start date)
    counter_start = start_date if start_date is not None else df_calc["date"].min().date()
    start_monday = counter_start - timedelta(days=counter_start.weekday())
    kw_summary["Week"] = kw_summary.apply(
        lambda r: (date.fromisocalendar(int(r["Year"]), int(r["KW"]), 1) - start_monday).days // 7 + 1,
        axis=1
    )
    st.dataframe(
        kw_summary[["Year", "KW", "Week", "Average", "Range", "Entries"]],
        width="stretch",
        hide_index=True
    )


# ====================================================
# QUOTE LIBRARY
# ====================================================
st.markdown("---")
with st.expander("📚 Quote Library"):
    if df_quotes.empty:
        st.caption("Your library is empty, so the built-in quotes are being used. Add your own below, or import the built-in ones to start from them.")
        if st.button("Import built-in quotes"):
            save_quotes(pd.DataFrame(MOTIVATIONAL_QUOTES, columns=["quote", "author"]))
            st.success("Built-in quotes imported!")
            st.rerun()

    with st.form("quote_form", clear_on_submit=True):
        new_quote = st.text_area("New quote", placeholder="e.g., Small progress is still progress.")
        new_author = st.text_input("Author (optional)")
        if st.form_submit_button("Add Quote", width="stretch"):
            if not new_quote.strip():
                st.error("Please enter a quote.")
            else:
                base_df = df_quotes[["quote", "author"]] if not df_quotes.empty else pd.DataFrame(columns=["quote", "author"])
                new_row = pd.DataFrame([{"quote": new_quote.strip(), "author": new_author.strip() or "Unknown"}])
                save_quotes(pd.concat([base_df, new_row], ignore_index=True))
                st.success("Quote added!")
                st.rerun()

    if not df_quotes.empty:
        st.markdown(f"**{len(df_quotes)} quotes in your library**")
        st.dataframe(df_quotes[["quote", "author"]], width="stretch", hide_index=True)
        labels = [f"{i+1}. {str(q)[:60]}{'…' if len(str(q)) > 60 else ''}" for i, q in enumerate(df_quotes["quote"])]
        to_delete = st.selectbox("Remove a quote", options=range(len(labels)), format_func=lambda i: labels[i])
        if st.button("Delete selected quote"):
            save_quotes(df_quotes.drop(index=to_delete)[["quote", "author"]].reset_index(drop=True))
            st.success("Quote removed.")
            st.rerun()
