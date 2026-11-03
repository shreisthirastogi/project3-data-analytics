import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Engineering Placement ROI Dashboard", layout="wide", page_icon="🎓")

@st.cache_data
def load_data():
    conn = sqlite3.connect("data/placements.db")
    df_clean = pd.read_sql_query("SELECT * FROM placements", conn)
    conn.close()
    df_fc = pd.read_csv("data/processed/prophet_forecasts.csv")
    df_bt = pd.read_csv("data/processed/backtest_metrics.csv")
    return df_clean, df_fc, df_bt

try:
    df, fc_df, bt_df = load_data()
except Exception as e:
    st.error(f"Please run the ETL and forecasting pipeline first! Error: {e}")
    st.stop()

st.title("🎓 Indian Engineering Placement ROI & Trajectory Dashboard")
st.markdown(
    "**Specialization & College-Tier Analytics (2016–2026)** | "
    "Powered by SQLite Window Functions & Facebook Prophet Forecasting"
)

# Sidebar Filters
st.sidebar.header("Filter Parameters")
selected_tiers = st.sidebar.multiselect(
    "Select College Tiers",
    options=["Tier 1", "Tier 2", "Tier 3"],
    default=["Tier 1", "Tier 2", "Tier 3"]
)

available_specs = sorted(df["specialization"].unique())
default_specs = [s for s in ["CSE", "AI/DS", "ECE", "Mechanical"] if s in available_specs]
selected_specs = st.sidebar.multiselect(
    "Select Specializations",
    options=available_specs,
    default=default_specs
)

selected_year = st.sidebar.slider("Snapshot Year for ROI Comparison", 2016, 2024, 2024)

filtered_df = df[
    (df["tier"].isin(selected_tiers)) &
    (df["specialization"].isin(selected_specs))
]

snap_df = filtered_df[filtered_df["year"] == selected_year]

# Top KPI Row
c1, c2, c3, c4 = st.columns(4)
if not snap_df.empty:
    c1.metric(f"Median Salary ({selected_year})", f"₹{snap_df['median_salary'].median():.2f} LPA")
    c2.metric(f"Avg Placement Rate ({selected_year})", f"{snap_df['placed_percentage'].mean():.1f}%")
    c3.metric("Best ROI Ratio (1st Yr Sal / Fee)", f"{snap_df['roi_ratio'].max():.2f}x")
else:
    c1.metric("Median Salary", "N/A")
    c2.metric("Avg Placement Rate", "N/A")
    c3.metric("Best ROI Ratio", "N/A")
c4.metric("Prophet Backtest Mean MAPE", f"{bt_df['mape_pct'].mean():.2f}%")

st.divider()

# Row 1: Salary Trends & ROI Scatter Plot
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("1. Starting Salary Trends Across Tiers (2016–2024)")
    trend_df = (
        filtered_df.groupby(["year", "tier", "specialization"], as_index=False)["median_salary"]
        .mean()
    )
    fig_trend = px.line(
        trend_df,
        x="year",
        y="median_salary",
        color="tier",
        line_dash="specialization",
        markers=True,
        labels={"median_salary": "Median Salary (LPA)", "year": "Academic Year"},
        title="Historical Salary Trajectory (in Lakhs INR/Year)"
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    st.subheader(f"2. Tuition Fee vs. Median Salary ({selected_year} ROI Scatter)")
    fig_scatter = px.scatter(
        snap_df,
        x="tuition_lpa",
        y="median_salary",
        color="tier",
        size="placed_percentage",
        hover_name="college_name",
        hover_data=["specialization", "roi_ratio"],
        labels={"tuition_lpa": "Total 4-Year Tuition (LPA)", "median_salary": "Median Salary (LPA)"},
        title=f"ROI Frontier: Bubble Size = Placement Rate % ({selected_year})"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# Row 2: Prophet Forecasting & SQL Window Ranks
col_fc, col_sql = st.columns(2)

with col_fc:
    st.subheader("3. Prophet Time-Series Forecast (2025–2026 Trajectory)")
    metric_choice = st.selectbox("Select Forecast Metric", ["median_salary", "placed_percentage"])
    spec_choice = st.selectbox("Select Specialization to Inspect", ["CSE", "AI/DS", "ECE"])

    sub_fc = fc_df[(fc_df["specialization"] == spec_choice) & (fc_df["metric"] == metric_choice)]

    fig_fc = go.Figure()
    colors = {"Tier 1": "#1f77b4", "Tier 2": "#ff7f0e", "Tier 3": "#2ca02c"}

    for t in selected_tiers:
        t_data = sub_fc[sub_fc["tier"] == t]
        if not t_data.empty:
            c = colors.get(t, "#333")
            # Upper bound
            fig_fc.add_trace(go.Scatter(
                x=t_data["year"], y=t_data["yhat_upper"],
                mode="lines", line=dict(width=0), showlegend=False,
                hoverinfo="skip"
            ))
            # Lower bound filled
            fig_fc.add_trace(go.Scatter(
                x=t_data["year"], y=t_data["yhat_lower"],
                mode="lines", line=dict(width=0),
                fill="tonexty", fillcolor=f"rgba(100,100,100,0.15)",
                showlegend=False, hoverinfo="skip"
            ))
            # Forecast prediction
            fig_fc.add_trace(go.Scatter(
                x=t_data["year"], y=t_data["yhat"],
                mode="lines+markers", name=f"{t} Forecast",
                line=dict(color=c, width=2.5)
            ))

    fig_fc.update_layout(
        title=f"{spec_choice} {metric_choice.replace('_', ' ').title()} Forecast to 2026",
        xaxis_title="Year",
        yaxis_title="Predicted Value",
    )
    st.plotly_chart(fig_fc, use_container_width=True)

with col_sql:
    st.subheader("4. Analytical SQL Window Function Output")
    st.caption("Demonstrating `RANK() OVER (PARTITION BY specialization, year ORDER BY yoy_growth DESC)` via SQLite")

    conn = sqlite3.connect("data/placements.db")
    with open("sql/analysis_queries.sql", "r", encoding="utf-8") as f:
        sql_script = f.read()
    q1 = [q.strip() for q in sql_script.split(";") if q.strip()][0]
    df_sql = pd.read_sql_query(q1, conn)
    conn.close()

    st.dataframe(df_sql, use_container_width=True, height=350)

st.divider()

# Section 5: Actionable Recommendation Engine
st.subheader("💡 Strategic Recommendations for Prospective Students")
col_rec1, col_rec2 = st.columns(2)

with col_rec1:
    st.info(
        "**Best Overall Value (Highest ROI Trajectory):**\n\n"
        "- **Tier-1 Public / NITs (e.g. NIT Trichy):** With 4-year fees under ₹7.5 LPA and median CSE/AI salaries exceeding ₹18 LPA, "
        "public Tier-1 colleges deliver an unprecedented **2.4x - 2.8x 1st-year ROI**.\n"
        "- **Tier-2 Govt/State (e.g. COEP Pune, DTU):** Deliver near-parity starting salaries to Tier-1 at half the tuition cost of private universities."
    )

with col_rec2:
    st.success(
        "**Specialization Outlook (2025–2026 Forecast):**\n\n"
        "- **AI/DS and CSE** continue to display the highest compound growth (>6.5% YoY), maintaining >90% placement rates across Tier 1 and Tier 2.\n"
        "- **High-Fee Tier-3 Private Universities:** Show an average ROI ratio of 0.35x - 0.50x, requiring 3-4 years longer to break even on tuition."
    )
