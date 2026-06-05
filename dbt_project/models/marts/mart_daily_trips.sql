-- marts/mart_daily_trips.sql
-- Final mart table: daily aggregated trip metrics by city.
-- This is the table Metabase/Looker Studio connects to.

{{ config(materialized='table') }}

SELECT
    trip_date,
    city,
    is_weekend,
    day_of_week,
    COUNT(trip_id)          AS total_trips,
    COUNT(DISTINCT driver_id) AS active_drivers,
    ROUND(AVG(fare_usd), 2) AS avg_fare_usd,
    ROUND(SUM(fare_usd), 2) AS total_revenue_usd,
    ROUND(MAX(fare_usd), 2) AS max_fare_usd,
    ROUND(MIN(fare_usd), 2) AS min_fare_usd
FROM {{ ref('stg_trips') }}
GROUP BY 1, 2, 3, 4
ORDER BY 1 DESC
