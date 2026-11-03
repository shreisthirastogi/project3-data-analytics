-- ============================================================================
-- FILE: sql/analysis_queries.sql
-- PROJECT 3: Placement ROI & Specialization Trajectory Analysis
-- DIALECT: SQLite 3.25+ / PostgreSQL Compatible Window Functions
-- ============================================================================

-- QUERY 1: Year-over-Year (YoY) Salary Growth & College Ranking per Specialization
-- Uses LAG() to fetch prior year salary and RANK() OVER (PARTITION BY specialization ...)
WITH salary_lag_cte AS (
    SELECT
        college_name,
        tier,
        specialization,
        year,
        median_salary,
        placed_percentage,
        roi_ratio,
        LAG(median_salary, 1) OVER (
            PARTITION BY college_name, specialization
            ORDER BY year
        ) AS prev_year_salary
    FROM placements
),
yoy_calculated_cte AS (
    SELECT
        college_name,
        tier,
        specialization,
        year,
        median_salary,
        prev_year_salary,
        placed_percentage,
        roi_ratio,
        ROUND(
            ((median_salary - prev_year_salary) / NULLIF(prev_year_salary, 0)) * 100.0,
            2
        ) AS yoy_growth
    FROM salary_lag_cte
    WHERE prev_year_salary IS NOT NULL
)
SELECT
    year,
    specialization,
    college_name,
    tier,
    median_salary,
    yoy_growth,
    RANK() OVER (
        PARTITION BY specialization, year
        ORDER BY yoy_growth DESC
    ) AS growth_rank_in_specialization
FROM yoy_calculated_cte
WHERE year = 2024
ORDER BY specialization, growth_rank_in_specialization ASC;

-- QUERY 2: Multi-Year Compound ROI & 3-Year Rolling Salary Average by Tier
-- Uses AVG() OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
SELECT
    tier,
    specialization,
    year,
    ROUND(AVG(median_salary), 2) AS current_year_median_sal,
    ROUND(AVG(roi_ratio), 2) AS avg_roi_ratio,
    ROUND(
        AVG(AVG(median_salary)) OVER (
            PARTITION BY tier, specialization
            ORDER BY year
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS rolling_3yr_avg_salary
FROM placements
GROUP BY tier, specialization, year
ORDER BY tier, specialization, year;

-- QUERY 3: Comprehensive Tier ROI & Placement Dominance (2024 Snapshot)
-- Combines DENSE_RANK() and placement efficiency ratios
SELECT
    tier,
    specialization,
    ROUND(AVG(median_salary), 2) AS avg_median_salary_lpa,
    ROUND(AVG(placed_percentage), 1) AS avg_placed_pct,
    ROUND(AVG(roi_ratio), 2) AS avg_roi_ratio,
    DENSE_RANK() OVER (ORDER BY AVG(roi_ratio) DESC) AS overall_roi_rank
FROM placements
WHERE year = 2024
GROUP BY tier, specialization
ORDER BY overall_roi_rank ASC;
