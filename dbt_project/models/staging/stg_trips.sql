-- staging/stg_trips.sql
-- Staging model: clean and type-cast raw ingested trip data.
-- Tests for nulls and duplicates are defined in schema.yml

{{ config(materialized='view') }}

SELECT
    CAST(trip_id     AS INTEGER)                 AS trip_id,
    CAST(driver_id   AS INTEGER)                 AS driver_id,
    CAST(fare        AS NUMERIC(10, 2))           AS fare_usd,
    CAST(date        AS DATE)                     AS trip_date,
    EXTRACT(DOW FROM CAST(date AS DATE))          AS day_of_week,  -- 0=Sun, 6=Sat
    CASE
        WHEN EXTRACT(DOW FROM CAST(date AS DATE)) IN (0, 6) THEN TRUE
        ELSE FALSE
    END                                           AS is_weekend,
    city,
    CURRENT_TIMESTAMP                             AS ingested_at
FROM {{ source('raw', 'raw_trips') }}
WHERE fare IS NOT NULL          -- Explicit filter; dbt test will also catch this
  AND trip_id IS NOT NULL
