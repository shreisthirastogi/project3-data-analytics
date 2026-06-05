"""
forecast.py — Standalone forecast + decision script for Project 3
Can be run locally (without Airflow) to test the forecasting layer.

Usage:
    python analysis/forecast.py

Outputs:
    - Printed MAPE, RMSE, decision recommendation
    - analysis/forecast_results.json
"""
import warnings
warnings.filterwarnings("ignore")

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────
# 1. GENERATE SYNTHETIC DATA (replace with real mart query)
# ─────────────────────────────────────────────────────────────
def generate_synthetic_trips(n_days: int = 90) -> pd.DataFrame:
    """
    Simulates 90 days of City X trip data with realistic weekend effects.
    Replace with: pd.read_sql("SELECT * FROM mart_daily_trips ...", conn)
    """
    np.random.seed(42)
    dates = pd.date_range(end=datetime.today(), periods=n_days, freq="D")
    records = []
    for d in dates:
        is_weekend = d.weekday() >= 5
        base_demand = 120 if is_weekend else 100
        base_drivers = 18 if is_weekend else 25   # Fewer drivers on weekends!
        records.append({
            "trip_date": d.date(),
            "is_weekend": is_weekend,
            "total_trips": int(base_demand + np.random.normal(0, 10)),
            "active_drivers": int(base_drivers + np.random.normal(0, 2)),
            "avg_fare_usd": round(20 + np.random.normal(0, 3), 2),
        })
    return pd.DataFrame(records)


# ─────────────────────────────────────────────────────────────
# 2. ARIMA FORECAST
# ─────────────────────────────────────────────────────────────
def run_arima_forecast(df: pd.DataFrame) -> dict:
    try:
        from statsmodels.tsa.arima.model import ARIMA
    except ImportError:
        print("statsmodels not installed. Run: pip install statsmodels")
        return {}

    series = pd.Series(df["total_trips"].values, index=pd.DatetimeIndex(df["trip_date"]))
    series.index.freq = "D"

    # Train / test split: last 14 days as test
    train, test = series[:-14], series[-14:]

    model = ARIMA(train, order=(1, 1, 1))
    fit = model.fit()
    forecast = fit.forecast(steps=14)

    # Metrics
    mape = float(np.mean(np.abs((test.values - forecast.values) / (test.values + 1e-9))) * 100)
    rmse = float(np.sqrt(np.mean((test.values - forecast.values) ** 2)))

    print(f"\n📈 ARIMA Forecast (14-day holdout)")
    print(f"   MAPE : {mape:.2f}%")
    print(f"   RMSE : {rmse:.2f} trips/day")

    return {
        "mape_pct": round(mape, 2),
        "rmse": round(rmse, 2),
        "test_actual": test.tolist(),
        "test_forecast": forecast.round(1).tolist(),
        "test_dates": [str(d.date()) for d in test.index],
    }


# ─────────────────────────────────────────────────────────────
# 3. DECISION ENGINE
# ─────────────────────────────────────────────────────────────
def make_business_decision(df: pd.DataFrame, forecast_results: dict) -> str:
    weekend = df[df["is_weekend"] == True]
    weekday = df[df["is_weekend"] == False]

    demand_ratio = weekend["total_trips"].mean() / weekday["total_trips"].mean()
    supply_gap = (weekday["active_drivers"].mean() - weekend["active_drivers"].mean()) / weekday["active_drivers"].mean() * 100

    print(f"\n📊 Signal Summary")
    print(f"   Weekend demand vs weekday : {demand_ratio:.2f}x")
    print(f"   Weekend supply gap        : {supply_gap:.1f}%")

    if supply_gap > 20 and demand_ratio > 1.05:
        decision = (
            f"✅ SHIP: Increase weekend driver incentives in City X by 15%. "
            f"Weekend demand is {demand_ratio:.1f}x weekday, yet driver supply "
            f"is {supply_gap:.1f}% lower. MAPE: {forecast_results.get('mape_pct', 'N/A')}%."
        )
    else:
        decision = (
            f"⛔ NO-SHIP: Gap insufficient to justify incentive spend. "
            f"Demand ratio: {demand_ratio:.2f}, supply gap: {supply_gap:.1f}%."
        )

    print(f"\n🎯 DECISION: {decision}")
    return decision


# ─────────────────────────────────────────────────────────────
# 4. MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("PROJECT 3 — FORECAST & DECISION ENGINE")
    print("=" * 60)

    df = generate_synthetic_trips(n_days=90)
    print(f"\nLoaded {len(df)} days of trip data ({df['trip_date'].min()} → {df['trip_date'].max()})")
    print(df.tail(5).to_string(index=False))

    forecast_results = run_arima_forecast(df)
    recommendation = make_business_decision(df, forecast_results)

    output = {
        "generated_at": datetime.now().isoformat(),
        "recommendation": recommendation,
        **forecast_results,
        "summary_stats": {
            "weekend_avg_trips": round(df[df["is_weekend"]]["total_trips"].mean(), 1),
            "weekday_avg_trips": round(df[~df["is_weekend"]]["total_trips"].mean(), 1),
            "weekend_avg_drivers": round(df[df["is_weekend"]]["active_drivers"].mean(), 1),
            "weekday_avg_drivers": round(df[~df["is_weekend"]]["active_drivers"].mean(), 1),
        },
    }

    with open("analysis/forecast_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\n✅ Results saved to analysis/forecast_results.json")
