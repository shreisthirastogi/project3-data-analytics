import os
import random
import numpy as np
import pandas as pd

np.random.seed(42)
random.seed(42)

def generate_datasets():
    os.makedirs("data/raw", exist_ok=True)

    # Canonical colleges with canonical Tier and average 4-year Total Tuition Fees (in Lakhs INR)
    colleges = [
        ("IIT Bombay", "Tier 1", 10.0),
        ("IIT Delhi", "Tier 1", 10.0),
        ("NIT Trichy", "Tier 1", 7.5),
        ("BITS Pilani", "Tier 1", 22.0),
        ("DTU Delhi", "Tier 2", 8.5),
        ("VIT Vellore", "Tier 2", 14.0),
        ("Thapar Institute", "Tier 2", 18.0),
        ("COEP Pune", "Tier 2", 6.0),
        ("Amity University Noida", "Tier 3", 15.0),
        ("Sharda University", "Tier 3", 11.0),
        ("Galgotias College", "Tier 3", 6.5),
        ("LPU Jalandhar", "Tier 3", 12.0),
    ]

    # Messy name variants to prove that clean_placement_data.py actually cleans messy data!
    messy_variants = {
        "IIT Bombay": ["IIT Bombay", "I.I.T. Bombay", "Indian Institute of Tech Bombay"],
        "IIT Delhi": ["IIT Delhi", "I.I.T Delhi", "Indian Inst of Tech Delhi"],
        "NIT Trichy": ["NIT Trichy", "N.I.T. Tiruchirappalli", "National Inst of Tech Trichy"],
        "BITS Pilani": ["BITS Pilani", "B.I.T.S. Pilani", "Birla Inst of Tech Pilani"],
        "DTU Delhi": ["DTU Delhi", "Delhi Technological Univ", "DCE / DTU Delhi"],
        "VIT Vellore": ["VIT Vellore", "Vellore Inst. of Tech", "V.I.T. Vellore"],
        "Thapar Institute": ["Thapar Institute", "Thapar Univ Patiala", "TIET Patiala"],
        "COEP Pune": ["COEP Pune", "College of Engg Pune", "C.O.E.P. Pune"],
        "Amity University Noida": ["Amity University Noida", "Amity Univ. Noida", "Amity Noida"],
        "Sharda University": ["Sharda University", "Sharda Univ Greater Noida"],
        "Galgotias College": ["Galgotias College", "Galgotias Engg College", "GCET Greater Noida"],
        "LPU Jalandhar": ["LPU Jalandhar", "Lovely Professional Univ", "L.P.U. Punjab"],
    }

    tier_variants = {
        "Tier 1": ["Tier 1", "tier 1", "tier-1"],
        "Tier 2": ["Tier 2", "tier 2", "tier-2"],
        "Tier 3": ["Tier 3", "tier 3", "tier-3"],
    }

    specializations = ["CSE", "AI/DS", "ECE", "Mechanical", "Civil"]
    tier_base_salary = {"Tier 1": 15.5, "Tier 2": 8.2, "Tier 3": 4.2}  # in LPA
    spec_multiplier = {"AI/DS": 1.32, "CSE": 1.25, "ECE": 1.00, "Mechanical": 0.72, "Civil": 0.65}
    tier_base_placed = {"Tier 1": 88.0, "Tier 2": 78.0, "Tier 3": 62.0}
    spec_placed_bonus = {"AI/DS": 6.5, "CSE": 5.5, "ECE": 1.0, "Mechanical": -6.0, "Civil": -9.0}

    all_records = []
    years = list(range(2016, 2025))  # 2016 to 2024 (9 years)

    for canonical_name, tier, tuition_lpa in colleges:
        for spec in specializations:
            for yr in years:
                # Year growth multiplier (approx 5-7% inflation/growth per year)
                year_offset = yr - 2016
                base_sal = tier_base_salary[tier] * spec_multiplier[spec]
                growth_factor = 1.0 + (0.055 * year_offset)
                noise_sal = np.random.normal(0, 0.4)
                sal = round(max(2.5, (base_sal * growth_factor) + noise_sal), 2)

                base_pl = tier_base_placed[tier] + spec_placed_bonus[spec]
                growth_pl = min(99.0, max(40.0, base_pl + (0.6 * year_offset) + np.random.normal(0, 1.8)))
                pl = round(growth_pl, 1)

                all_records.append({
                    "canonical_name": canonical_name,
                    "tier": tier,
                    "tuition_lpa": tuition_lpa,
                    "specialization": spec,
                    "year": yr,
                    "median_salary": sal,
                    "placed_percentage": pl,
                })

    df_master = pd.DataFrame(all_records)

    # 1. Dataset 1: AICTE placements (2016 to 2020)
    df_part1 = df_master[df_master["year"] <= 2020].copy()
    # Canonical or slight variations
    df_part1["college_name"] = df_part1["canonical_name"]
    df_part1["tier"] = df_part1["tier"]
    p1_cols = ["college_name", "tier", "specialization", "year", "placed_percentage", "median_salary", "tuition_lpa"]
    df_part1[p1_cols].to_csv("data/raw/aicte_placements_part1.csv", index=False)
    print(f"[Dataset 1] Generated aicte_placements_part1.csv with {len(df_part1)} rows.")

    # 2. Dataset 2: NIRF Tier placements (2020 to 2024) with intentionally messy names & tier formatting
    df_part2 = df_master[df_master["year"] >= 2020].copy()
    df_part2["college_name"] = df_part2["canonical_name"].apply(
        lambda name: random.choice(messy_variants.get(name, [name]))
    )
    df_part2["tier"] = df_part2["tier"].apply(
        lambda t: random.choice(tier_variants.get(t, [t]))
    )
    df_part2[p1_cols].to_csv("data/raw/nirf_tier_placements_part2.csv", index=False)
    print(f"[Dataset 2] Generated nirf_tier_placements_part2.csv with {len(df_part2)} rows.")

    # 3. Dataset 3: Kaggle historical gaps (supplemental records with intentional year gaps & duplicate noise)
    df_part3 = df_master.sample(frac=0.45, random_state=42).copy()
    df_part3["college_name"] = df_part3["canonical_name"].apply(
        lambda name: random.choice(messy_variants.get(name, [name]))
    )
    df_part3["tier"] = df_part3["tier"].apply(
        lambda t: random.choice(tier_variants.get(t, [t]))
    )
    df_part3[p1_cols].to_csv("data/raw/kaggle_historical_gaps.csv", index=False)
    print(f"[Dataset 3] Generated kaggle_historical_gaps.csv with {len(df_part3)} rows.")

if __name__ == "__main__":
    generate_datasets()
