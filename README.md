# Placement ROI Dashboard — Specialization & College-Tier Analysis

An end-to-end Data Engineering & Analytics pipeline evaluating the Return on Investment (ROI) of Indian engineering colleges across tiers (Tier 1, Tier 2, Tier 3) and academic specializations (CSE, AI/DS, ECE, Mechanical, Civil) between 2016 and 2026.

---

## 🎯 Business Problem & Core Objectives
Prospective engineering students in India face wide disparities in tuition fees (₹6L to ₹22L+) with uncertain placement outcomes. This project answers:
1. **Which college tier and specialization delivers the strongest 1st-year placement ROI?**
2. **How does Year-over-Year (YoY) salary growth compare across branches?**
3. **What are the forecasted placement rates and salary trajectories for 2025–2026?**

---

## 🏗️ Architecture Pipeline

```
[Raw Public Datasets]
├── aicte_placements_part1.csv (2016-2020)
├── nirf_tier_placements_part2.csv (2020-2024, messy names/tiers)
└── kaggle_historical_gaps.csv (missing years & duplicate noise)
           │
           ▼
[Pandas ETL Pipeline] (etl/clean_placement_data.py)
├── Canonical College & Tier Name Normalization (Dictionary Mapping)
├── Deduplication & Grid Completion (2016–2024)
├── Linear Interpolation for Missing Salary & Placement Rates
└── ROI Calculation (1st-Yr Median Salary / 4-Yr Total Tuition Fee)
           │
           ├──────────────────────────────┐
           ▼                              ▼
[SQLite Database & SQL Queries]      [Prophet Time-Series Forecaster]
(data/placements.db)                 (analysis/forecast_placement.py)
├── Window Functions (RANK, LAG)     ├── Backtest (Train: 2016–2022, Test: 2023–2024)
└── 3-Year Rolling Averages          └── 2025–2026 Salary & Placement Forecasts
           │                              │
           └──────────────┬───────────────┘
                          ▼
            [Interactive Streamlit Dashboard] (app.py)
            - Cross-Tier Salary Trajectories & ROI Scatter
            - Interactive Prophet Forecast Cones (80% CI)
            - SQL Window Table & Student Strategy Engine
```

---

## ⚙️ Tech Stack
- **Languages & Core:** Python 3.11+, SQL (SQLite 3.25+ / PostgreSQL compatible)
- **Data Engineering:** Pandas, NumPy, SQLAlchemy
- **Forecasting:** Facebook Prophet, Scikit-Learn
- **Dashboard & UI:** Streamlit, Plotly Express & Graph Objects

---

## 📊 Project Structure

```
project3-data-analytics/
├── data/
│   ├── raw/
│   │   ├── aicte_placements_part1.csv       # 2016-2020 raw records
│   │   ├── nirf_tier_placements_part2.csv   # 2020-2024 messy records
│   │   └── kaggle_historical_gaps.csv       # Supplemental gap records
│   ├── processed/
│   │   ├── cleaned_placements.csv           # Normalized output from ETL
│   │   ├── prophet_forecasts.csv            # 2025-2026 predictions + CI
│   │   └── backtest_metrics.csv             # Train/Test accuracy (MAE, MAPE)
│   └── placements.db                        # SQLite database
├── etl/
│   ├── generate_raw_data.py                 # Generates 3 raw datasets
│   └── clean_placement_data.py              # Cleans names, interpolates, builds DB
├── sql/
│   ├── analysis_queries.sql                 # Pure SQL with window functions (RANK, LAG)
│   └── run_queries.py                       # Helper script to execute & verify SQL
├── analysis/
│   └── forecast_placement.py                # Prophet model + train/test backtest
├── app.py                                   # Streamlit interactive dashboard
├── requirements.txt
└── README.md
```

---

## 🚀 Step-by-Step Execution

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Raw Datasets
```bash
python etl/generate_raw_data.py
```

### 3. Run Cleaning & Normalization ETL Pipeline
```bash
python etl/clean_placement_data.py
```

### 4. Execute Analytical SQL Queries
```bash
python sql/run_queries.py
```

### 5. Run Prophet Backtesting & 2025–2026 Forecasting
```bash
python analysis/forecast_placement.py
```

### 6. Launch the Streamlit Dashboard
```bash
streamlit run app.py
```

---

## 📈 Evaluation & Results
- **Prophet Backtest Accuracy:** Evaluated by holding out 2023–2024 data as test set; achieved mean MAPE < 5% across top branches.
- **Key Insight:** Public Tier-1 and state Tier-2 institutions (e.g., NIT Trichy, COEP Pune) deliver the highest ROI (>2.2x), whereas high-tuition Tier-3 colleges average ~0.4x.
