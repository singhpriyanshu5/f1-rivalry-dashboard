-- Pit stop data from Jolpica API
-- Flattens VARIANT array into one row per (season, round, driver_id, stop)

with raw as (
    select
        season,
        round,
        raw_data,
        _ingested_at
    from {{ source('raw', 'raw_jolpica_pit_stops') }}
),

flattened as (
    select
        r.season,
        r.round,
        q.value:driverId::varchar as driver_id,
        q.value:stop::integer as stop_number,
        q.value:lap::integer as lap_number,
        q.value:duration::varchar as duration_str,
        q.value:time::varchar as time_of_day,
        r._ingested_at
    from raw r,
    lateral flatten(input => r.raw_data) q
)

select
    season,
    round,
    driver_id,
    stop_number,
    lap_number,
    duration_str,
    time_of_day,
    -- Parse duration string "SS.mmm" to seconds
    case
        when duration_str is not null and duration_str != ''
             and not contains(duration_str, ':') then
            duration_str::float
        when duration_str is not null and contains(duration_str, ':') then
            split_part(duration_str, ':', 1)::float * 60
            + split_part(duration_str, ':', 2)::float
    end as pit_duration_s,
    _ingested_at
from flattened
