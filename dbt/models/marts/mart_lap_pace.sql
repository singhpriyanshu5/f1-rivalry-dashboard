-- Teammate lap pace comparison per round
-- Joins laps with results to get constructor context (more complete than qualifying)
-- Filters safety car laps (>1.5x median lap time per round)

with driver_constructors as (
    select distinct
        season,
        round,
        driver_id,
        driver_code,
        constructor_id,
        constructor_name
    from {{ ref('stg_results') }}
),

laps_with_team as (
    select
        l.season,
        l.round,
        l.lap_number,
        l.driver_id,
        dc.driver_code,
        dc.constructor_id,
        dc.constructor_name,
        l.lap_time_s,
        l.position
    from {{ ref('stg_laps') }} l
    inner join driver_constructors dc
        on l.season = dc.season
        and l.round = dc.round
        and l.driver_id = dc.driver_id
    where l.lap_time_s is not null
),

-- Median lap time per round to filter safety car laps
round_medians as (
    select
        season,
        round,
        median(lap_time_s) as median_lap_s
    from laps_with_team
    group by season, round
),

filtered as (
    select lwt.*
    from laps_with_team lwt
    inner join round_medians rm
        on lwt.season = rm.season
        and lwt.round = rm.round
    where lwt.lap_time_s <= rm.median_lap_s * 1.5
)

select
    f.season,
    f.round,
    f.lap_number,
    f.driver_id,
    f.driver_code,
    f.constructor_id,
    f.constructor_name,
    f.lap_time_s,
    f.position,
    dr.round_label,
    dr.locality
from filtered f
left join {{ ref('dim_races') }} dr
    on f.season = dr.season and f.round = dr.round
