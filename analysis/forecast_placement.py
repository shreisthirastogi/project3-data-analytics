import logging
import os
import sqlite3
import warnings
import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

# Silence verbose cmdstanpy & prophet logs
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.WARNING)
warnings.filterwarnings("ignore")

TARGET_SPECS = ["CSE", "AI/DS", "ECE"]
METRICS = ["median_salary", "placed_percentage"]

def fit_and_predict_prophet(df_series, periods=2):
    """Fits a Prophet model on annual data (ds, y) and predicts `periods` years ahead."""
    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.15,
        interval_width=0.80
    )
    model.fit(df_series[["ds", "y"]])
    future = model.make_future_dataframe(periods=periods, freq="YS")
    forecast = model.predict(future)
    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]

def run_prophet_backtest_and_forecast():
    os.makedirs("data/processed", exist_ok=True)
    conn = sqlite3.connect("data/placements.db")
    df = pd.read_sql_query("SELECT * FROM placements", conn)
    conn.close()

    # Filter for top specializations and aggregate by Tier + Specialization + Year
    sub_df = (
        df[df["specialization"].isin(TARGET_SPECS)]
        .groupby(["tier", "specialization", "year"], as_index=False)
        .agg({"median_salary": "mean", "placed_percentage": "mean"})
    )

    backtest_rows = []
    forecast_rows = []

    print("[Prophet] Starting Backtest (Train: 2016-2022 | Test: 2023-2024)...")

    for (tier, spec), group in sub_df.groupby(["tier", "specialization"]):
        group = group.sort_values("year").reset_index(drop=True)
        group["ds"] = pd.to_datetime(group["year"].astype(str) + "-01-01")

        for metric in METRICS:
            series_df = group[["ds", "year", metric]].rename(columns={metric: "y"}).copy()

            # --- STEP A: Train/Test Backtest (Train: 2016-2022, Test: 2023-2024) ---
            train_df = series_df[series_df["year"] <= 2022].copy()
            test_df = series_df[series_df["year"] > 2022].copy()

            bt_pred = fit_and_predict_prophet(train_df, periods=len(test_df))
            bt_eval = pd.merge(test_df, bt_pred, on="ds", how="inner")

            mae = mean_absolute_error(bt_eval["y"], bt_eval["yhat"])
            mape = mean_absolute_percentage_error(bt_eval["y"], bt_eval["yhat"]) * 100.0

            backtest_rows.append({
                "tier": tier,
                "specialization": spec,
                "metric": metric,
                "train_years": "2016-2022",
                "test_years": "2023-2024",
                "mae": round(mae, 2),
                "mape_pct": round(mape, 2),
            })

            # --- STEP B: Full Horizon Refit & 2025-2026 Future Forecast ---
            fc_future = fit_and_predict_prophet(series_df, periods=2)
            fc_future["tier"] = tier
            fc_future["specialization"] = spec
            fc_future["metric"] = metric
            fc_future["year"] = fc_future["ds"].dt.year
            forecast_rows.append(fc_future)

    # Save Backtest Metrics
    df_backtest = pd.DataFrame(backtest_rows)
    df_backtest.to_csv("data/processed/backtest_metrics.csv", index=False)
    print("\n[Prophet] Backtest Complete. Mean MAPE across all models:")
    print(f"--> Average MAPE: {df_backtest['mape_pct'].mean():.2f}%")
    print(df_backtest.to_string(index=False))

    # Save Future Forecasts
    df_forecast = pd.concat(forecast_rows, ignore_index=True)
    df_forecast["yhat"] = df_forecast["yhat"].round(2)
    df_forecast["yhat_lower"] = df_forecast["yhat_lower"].round(2)
    df_forecast["yhat_upper"] = df_forecast["yhat_upper"].round(2)
    df_forecast.to_csv("data/processed/prophet_forecasts.csv", index=False)
    print("\n[Prophet] Saved forecasts for 2025-2026 to data/processed/prophet_forecasts.csv.")

if __name__ == "__main__":
    run_prophet_backtest_and_forecast()
