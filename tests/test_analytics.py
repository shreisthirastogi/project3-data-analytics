import os
import sqlite3
import pandas as pd
import pytest

DB_PATH = "data/placements.db"
FC_PATH = "data/processed/prophet_forecasts.csv"
BT_PATH = "data/processed/backtest_metrics.csv"

def test_database_integrity():
    assert os.path.exists(DB_PATH), "Database file missing"
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM placements", conn)
    conn.close()

    assert len(df) == 540, f"Expected 540 records, found {len(df)}"
    # Check no nulls
    assert df["median_salary"].isnull().sum() == 0, "Found nulls in median_salary"
    assert df["placed_percentage"].isnull().sum() == 0, "Found nulls in placed_percentage"
    assert df["roi_ratio"].isnull().sum() == 0, "Found nulls in roi_ratio"

    # Verify tiers and colleges
    assert set(df["tier"].unique()) == {"Tier 1", "Tier 2", "Tier 3"}
    assert len(df["college_name"].unique()) == 12
    assert len(df["specialization"].unique()) == 5
    assert set(df["year"].unique()) == set(range(2016, 2025))

def test_sql_window_functions():
    conn = sqlite3.connect(DB_PATH)
    with open("sql/analysis_queries.sql", "r", encoding="utf-8") as f:
        sql_script = f.read()

    queries = [q.strip() for q in sql_script.split(";") if q.strip()]
    assert len(queries) >= 3, "Expected at least 3 analytical SQL queries"

    # Query 1: YoY Growth with RANK()
    df_q1 = pd.read_sql_query(queries[0], conn)
    assert "growth_rank_in_specialization" in df_q1.columns
    assert "yoy_growth" in df_q1.columns
    assert len(df_q1) > 0

    # Query 2: Rolling 3-year average
    df_q2 = pd.read_sql_query(queries[1], conn)
    assert "rolling_3yr_avg_salary" in df_q2.columns
    assert len(df_q2) > 0

    # Query 3: Multi-tier ROI comparison
    df_q3 = pd.read_sql_query(queries[2], conn)
    assert "overall_roi_rank" in df_q3.columns
    conn.close()

def test_prophet_forecast_and_backtest():
    assert os.path.exists(BT_PATH), "Backtest metrics file missing"
    assert os.path.exists(FC_PATH), "Forecasts file missing"

    df_bt = pd.read_csv(BT_PATH)
    assert "mape_pct" in df_bt.columns
    mean_mape = df_bt["mape_pct"].mean()
    assert mean_mape < 10.0, f"Expected MAPE < 10%, got {mean_mape}%"

    df_fc = pd.read_csv(FC_PATH)
    assert 2025 in df_fc["year"].values
    assert 2026 in df_fc["year"].values
    assert "yhat" in df_fc.columns
    assert "yhat_lower" in df_fc.columns
    assert "yhat_upper" in df_fc.columns
