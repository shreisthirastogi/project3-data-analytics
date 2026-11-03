import glob
import os
import sqlite3
import pandas as pd
import numpy as np

# Dictionary mapping messy raw strings to canonical college names
COLLEGE_NAME_MAPPING = {
    "IIT Bombay": "IIT Bombay",
    "I.I.T. Bombay": "IIT Bombay",
    "Indian Institute of Tech Bombay": "IIT Bombay",
    "IIT Delhi": "IIT Delhi",
    "I.I.T Delhi": "IIT Delhi",
    "Indian Inst of Tech Delhi": "IIT Delhi",
    "NIT Trichy": "NIT Trichy",
    "N.I.T. Tiruchirappalli": "NIT Trichy",
    "National Inst of Tech Trichy": "NIT Trichy",
    "BITS Pilani": "BITS Pilani",
    "B.I.T.S. Pilani": "BITS Pilani",
    "Birla Inst of Tech Pilani": "BITS Pilani",
    "DTU Delhi": "DTU Delhi",
    "Delhi Technological Univ": "DTU Delhi",
    "DCE / DTU Delhi": "DTU Delhi",
    "VIT Vellore": "VIT Vellore",
    "Vellore Inst. of Tech": "VIT Vellore",
    "V.I.T. Vellore": "VIT Vellore",
    "Thapar Institute": "Thapar Institute",
    "Thapar Univ Patiala": "Thapar Institute",
    "TIET Patiala": "Thapar Institute",
    "COEP Pune": "COEP Pune",
    "College of Engg Pune": "COEP Pune",
    "C.O.E.P. Pune": "COEP Pune",
    "Amity University Noida": "Amity University Noida",
    "Amity Univ. Noida": "Amity University Noida",
    "Amity Noida": "Amity University Noida",
    "Sharda University": "Sharda University",
    "Sharda Univ Greater Noida": "Sharda University",
    "Galgotias College": "Galgotias College",
    "Galgotias Engg College": "Galgotias College",
    "GCET Greater Noida": "Galgotias College",
    "LPU Jalandhar": "LPU Jalandhar",
    "Lovely Professional Univ": "LPU Jalandhar",
    "L.P.U. Punjab": "LPU Jalandhar",
}

TIER_MAPPING = {
    "tier 1": "Tier 1", "tier-1": "Tier 1", "Tier 1": "Tier 1",
    "tier 2": "Tier 2", "tier-2": "Tier 2", "Tier 2": "Tier 2",
    "tier 3": "Tier 3", "tier-3": "Tier 3", "Tier 3": "Tier 3",
}

def clean_and_load_pipeline():
    raw_files = glob.glob("data/raw/*.csv")
    if not raw_files:
        raise FileNotFoundError("No CSV files found in data/raw/. Run etl/generate_raw_data.py first!")

    # 1. Extract & Concatenate all raw public datasets
    df_list = [pd.read_csv(f) for f in raw_files]
    raw_df = pd.concat(df_list, ignore_index=True)
    print(f"[ETL] Loaded {len(raw_df)} raw rows across {len(raw_files)} files.")

    # 2. Normalize College Names via dictionary mapping
    raw_df["college_name"] = raw_df["college_name"].astype(str).str.strip().map(
        lambda name: COLLEGE_NAME_MAPPING.get(name, name)
    )

    # 3. Standardize Tier format
    raw_df["tier"] = raw_df["tier"].astype(str).str.strip().map(
        lambda t: TIER_MAPPING.get(t, "Tier 3")
    )

    # 4. Clean numeric columns
    raw_df["year"] = raw_df["year"].astype(int)
    raw_df["placed_percentage"] = pd.to_numeric(raw_df["placed_percentage"], errors="coerce")
    raw_df["median_salary"] = pd.to_numeric(raw_df["median_salary"], errors="coerce")
    raw_df["tuition_lpa"] = pd.to_numeric(raw_df["tuition_lpa"], errors="coerce")

    # 5. Deduplicate across multiple overlapping datasets
    dedup_df = (
        raw_df.groupby(["college_name", "tier", "specialization", "year"], as_index=False)
        .agg({
            "placed_percentage": "mean",
            "median_salary": "mean",
            "tuition_lpa": "first",
        })
    )
    print(f"[ETL] Deduplicated to {len(dedup_df)} unique (college, spec, year) records.")

    # 6. Complete time grid (2016-2024) and interpolate missing gaps
    all_years = list(range(2016, 2025))
    cleaned_records = []

    for (college, tier, spec), group in dedup_df.groupby(["college_name", "tier", "specialization"]):
        group = group.set_index("year").reindex(all_years)
        group["college_name"] = college
        group["tier"] = tier
        group["specialization"] = spec
        group["tuition_lpa"] = group["tuition_lpa"].bfill().ffill()

        # Linear interpolation for missing years
        group["placed_percentage"] = group["placed_percentage"].interpolate(method="linear").bfill().ffill()
        group["median_salary"] = group["median_salary"].interpolate(method="linear").bfill().ffill()
        group = group.reset_index().rename(columns={"index": "year"})
        cleaned_records.append(group)

    final_df = pd.concat(cleaned_records, ignore_index=True)

    # 7. Calculate ROI ratio (1st year median salary / total 4-year tuition fee)
    final_df["median_salary"] = final_df["median_salary"].round(2)
    final_df["placed_percentage"] = final_df["placed_percentage"].round(1)
    final_df["tuition_lpa"] = final_df["tuition_lpa"].round(2)
    final_df["roi_ratio"] = (final_df["median_salary"] / final_df["tuition_lpa"]).round(2)

    # 8. Export to Processed CSV & SQLite Database
    os.makedirs("data/processed", exist_ok=True)
    csv_path = "data/processed/cleaned_placements.csv"
    final_df.to_csv(csv_path, index=False)
    print(f"[ETL] Saved cleaned dataset to {csv_path} ({len(final_df)} records).")

    db_path = "data/placements.db"
    conn = sqlite3.connect(db_path)
    final_df.to_sql("placements", conn, if_exists="replace", index=False)

    # Create indices for analytical performance
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_spec_year ON placements(specialization, year);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tier_year ON placements(tier, year);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_college ON placements(college_name);")
    conn.commit()
    conn.close()

    print(f"[ETL] Loaded normalized placements table into SQLite: {db_path}")

if __name__ == "__main__":
    clean_and_load_pipeline()
