# ==========================================
# Project DAWN – Streamlit Interface
# Role: Interface layer (UI only)
# Data source: /data (live or last-good)
# ==========================================

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from connectors.csv_connector import load_events_from_csv, load_events_from_directory
from dawn.pipeline import run_pipeline


st.set_page_config(page_title="Project DAWN v0.1", layout="wide")

st.title("Project DAWN v0.1")
st.write("Upload CSV files or use the sample data in `data/raw/` to build a clean event feed.")

raw_dir = Path("data/raw")
raw_dir.mkdir(parents=True, exist_ok=True)

live_dir = Path("data/live")
live_dir.mkdir(parents=True, exist_ok=True)

live_file = live_dir / "dawn_live_data.csv"
last_good_file = live_dir / "last_good.csv"

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
raw_files = sorted([path.name for path in raw_dir.glob("*.csv")])
selected_raw_file = st.selectbox("Or select a CSV from data/raw", ["-- None --"] + raw_files)

st.divider()
st.subheader("Live Feed")
st.caption("If a collector writes to data/live/dawn_live_data.csv, you can load it here.")

use_live = st.checkbox("Use live feed file", value=live_file.exists())

colA, colB = st.columns([1, 2])
with colA:
    refresh_live = st.button("Refresh Live Feed")
with colB:
    st.write(f"Live file: `{live_file}`")
    st.write("Status:", "✅ found" if live_file.exists() else "❌ not found")

run_clicked = st.button("Run Pipeline")

if run_clicked or refresh_live:
    events = []

    # 1) Live feed (if chosen)
    if use_live:
        if live_file.exists():
            try:
                events.extend(load_events_from_csv(live_file))
            except Exception as e:
                st.error(f"Failed to read live file: {e}")
                # fallback to last known good
                if last_good_file.exists():
                    st.warning("Falling back to last_good.csv")
                    events.extend(load_events_from_csv(last_good_file))
        elif last_good_file.exists():
            st.warning("Live file not found. Using last_good.csv")
            events.extend(load_events_from_csv(last_good_file))

    # 2) Manual upload
    if uploaded_file is not None:
        events.extend(load_events_from_csv(uploaded_file))

    # 3) Manual raw selection
    if selected_raw_file != "-- None --":
        events.extend(load_events_from_csv(raw_dir / selected_raw_file))

    if not events:
        st.warning("No data found. Upload/select a CSV or enable live feed.")
    else:
        result = run_pipeline(events)
        st.session_state["events"] = result.events
        st.success(f"Processed {result.total_input} events (deduplicated {result.deduplicated}).")

        if use_live:
            st.caption("Live feed loaded (read-only). Collector manages persistence.")
        else:
            st.caption("Manual data loaded (upload / data/raw).")

if "events" not in st.session_state:
    with st.expander("Need data? Load all CSVs in data/raw"):
        if st.button("Load data/raw"):
            events = load_events_from_directory(raw_dir)
            if events:
                result = run_pipeline(events)
                st.session_state["events"] = result.events
                st.success(
                    f"Processed {result.total_input} events (deduplicated {result.deduplicated})."
                )
            else:
                st.info("No CSV files found in data/raw.")

if "events" in st.session_state:
    df = pd.DataFrame([event.model_dump() for event in st.session_state["events"]])
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True)
    df["date"] = df["published_at"].dt.date

    st.sidebar.header("Filters")
    company_options = ["All"] + sorted(df["company"].dropna().unique().tolist())
    publisher_options = ["All"] + sorted(df["publisher"].dropna().unique().tolist())
    theme_options = ["All"] + sorted(df["theme"].dropna().unique().tolist())
    sentiment_options = ["All"] + sorted(df["sentiment"].dropna().unique().tolist())

    selected_company = st.sidebar.selectbox("Company", company_options)
    selected_publisher = st.sidebar.selectbox("Publisher", publisher_options)
    selected_theme = st.sidebar.selectbox("Theme", theme_options)
    selected_sentiment = st.sidebar.selectbox("Sentiment", sentiment_options)
    trigger_only = st.sidebar.checkbox("Trigger events only")

    min_date = df["date"].min()
    max_date = df["date"].max()
    date_range = st.sidebar.date_input("Date range", (min_date, max_date))
    if isinstance(date_range, tuple):
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    filtered = df.copy()
    if selected_company != "All":
        filtered = filtered[filtered["company"] == selected_company]
    if selected_publisher != "All":
        filtered = filtered[filtered["publisher"] == selected_publisher]
    if selected_theme != "All":
        filtered = filtered[filtered["theme"] == selected_theme]
    if selected_sentiment != "All":
        filtered = filtered[filtered["sentiment"] == selected_sentiment]
    if trigger_only:
        filtered = filtered[filtered["is_trigger_event"]]

    filtered = filtered[(filtered["date"] >= start_date) & (filtered["date"] <= end_date)]

    st.subheader("Events")
    st.dataframe(filtered, use_container_width=True)

    st.subheader("Analytics")
    col1, col2, col3 = st.columns(3)

    sentiment_chart = (
        alt.Chart(filtered)
        .mark_bar()
        .encode(
            x=alt.X("sentiment:N", sort="-y"),
            y=alt.Y("count():Q", title="Count"),
            color="sentiment:N",
        )
    )

    volume_chart = (
        alt.Chart(filtered)
        .mark_line(point=True)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("count():Q", title="Events"),
        )
    )

    impact_chart = (
        alt.Chart(filtered)
        .mark_line(point=True)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("mean(impact_score):Q", title="Avg impact"),
        )
    )

    col1.altair_chart(sentiment_chart, use_container_width=True)
    col2.altair_chart(volume_chart, use_container_width=True)
    col3.altair_chart(impact_chart, use_container_width=True)

    st.subheader("Export")
    csv_data = filtered.drop(columns=["date"]).to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered CSV",
        data=csv_data,
        file_name=f"dawn_events_{datetime.utcnow().date()}.csv",
        mime="text/csv",
    )
