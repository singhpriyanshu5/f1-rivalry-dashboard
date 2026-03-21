-- Lap pace consistency summary per driver per round
-- Aggregates median, stddev, P25/P75, and lap count from filtered lap data
-- Used for consistency scoring and pace cloud visualization

with pace_data as (
    select
        season,
        round,
        round_label,
        locality,
        driver_id,
        driver_code,
        constructor_id,
        constructor_name,
        lap_time_s
    from {{ ref('mart_lap_pace') }}
),

driver_round_stats as (
    select
        season,
        round,
        round_label,
        locality,
        driver_id,
        driver_code,
        constructor_id,
        constructor_name,
        count(*) as lap_count,
        round(avg(lap_time_s), 3) as avg_lap_s,
        round(median(lap_time_s), 3) as median_lap_s,
        round(stddev(lap_time_s), 3) as stddev_lap_s,
        round(percentile_cont(0.25) within group (order by lap_time_s), 3) as p25_lap_s,
        round(percentile_cont(0.75) within group (order by lap_time_s), 3) as p75_lap_s,
        round(min(lap_time_s), 3) as fastest_lap_s,
        round(max(lap_time_s), 3) as slowest_lap_s
    from pace_data
    group by season, round, round_label, locality, driver_id, driver_code, constructor_id, constructor_name
)

select
    *,
    round(p75_lap_s - p25_lap_s, 3) as iqr_s,
    -- Consistency score: lower IQR = more consistent, scale to 0-100
    -- Uses IQR/median ratio (robust to outliers like pit in/out laps).
    -- Typical range: 0.005 (robot-like) to 0.06 (erratic).
    -- Ratio of 0 = score 100, ratio >= 0.06 = score 0.
    case
        when median_lap_s > 0 and p75_lap_s is not null and p25_lap_s is not null
        then round(greatest(100.0 * (1.0 - least((p75_lap_s - p25_lap_s) / median_lap_s, 0.06) / 0.06), 0), 1)
        else null
    end as consistency_score
from driver_round_stats
