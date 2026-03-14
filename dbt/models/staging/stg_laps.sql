-- Lap timing data from Jolpica API
-- Flattens VARIANT array into one row per (season, round, lap_number, driver_id)
-- Parses "M:SS.mmm" time strings to seconds

with raw as (
    select
        season,
        round,
        raw_data,
        _ingested_at
    from {{ source('raw', 'raw_jolpica_laps') }}
),

flattened as (
    select
        r.season,
        r.round,
        q.value:lap_number::integer as lap_number,
        q.value:driver_id::varchar as driver_id,
        q.value:position::integer as position,
        q.value:time::varchar as time_str,
        r._ingested_at
    from raw r,
    lateral flatten(input => r.raw_data) q
)

select
    season,
    round,
    lap_number,
    driver_id,
    position,
    time_str,
    -- Parse "M:SS.mmm" to seconds
    case
        when time_str is not null and time_str != '' then
            split_part(time_str, ':', 1)::float * 60
            + split_part(split_part(time_str, ':', 2), '.', 1)::float
            + split_part(time_str, '.', 2)::float / 1000
    end as lap_time_s,
    _ingested_at
from flattened
