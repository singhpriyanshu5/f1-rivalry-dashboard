with raw as (
    select
        season,
        round,
        raw_data,
        _ingested_at
    from {{ source('raw', 'raw_qualifying') }}
),

flattened as (
    select
        r.season,
        r.round,
        q.value:Driver:driverId::varchar as driver_id,
        q.value:Driver:code::varchar as driver_code,
        q.value:Driver:givenName::varchar || ' ' || q.value:Driver:familyName::varchar as driver_name,
        q.value:Constructor:constructorId::varchar as constructor_id,
        q.value:Constructor:name::varchar as constructor_name,
        q.value:position::integer as position,
        q.value:Q1::varchar as q1_time_str,
        q.value:Q2::varchar as q2_time_str,
        q.value:Q3::varchar as q3_time_str,
        r._ingested_at
    from raw r,
    lateral flatten(input => r.raw_data) q
)

select
    season,
    round,
    driver_id,
    driver_code,
    driver_name,
    constructor_id,
    constructor_name,
    position,
    -- Parse "M:SS.mmm" time strings to milliseconds
    case
        when q1_time_str is not null and q1_time_str != '' then
            split_part(q1_time_str, ':', 1)::integer * 60000
            + split_part(split_part(q1_time_str, ':', 2), '.', 1)::integer * 1000
            + split_part(q1_time_str, '.', 2)::integer
    end as q1_time_ms,
    case
        when q2_time_str is not null and q2_time_str != '' then
            split_part(q2_time_str, ':', 1)::integer * 60000
            + split_part(split_part(q2_time_str, ':', 2), '.', 1)::integer * 1000
            + split_part(q2_time_str, '.', 2)::integer
    end as q2_time_ms,
    case
        when q3_time_str is not null and q3_time_str != '' then
            split_part(q3_time_str, ':', 1)::integer * 60000
            + split_part(split_part(q3_time_str, ':', 2), '.', 1)::integer * 1000
            + split_part(q3_time_str, '.', 2)::integer
    end as q3_time_ms,
    coalesce(
        case when q3_time_str is not null and q3_time_str != '' then
            split_part(q3_time_str, ':', 1)::integer * 60000
            + split_part(split_part(q3_time_str, ':', 2), '.', 1)::integer * 1000
            + split_part(q3_time_str, '.', 2)::integer
        end,
        case when q2_time_str is not null and q2_time_str != '' then
            split_part(q2_time_str, ':', 1)::integer * 60000
            + split_part(split_part(q2_time_str, ':', 2), '.', 1)::integer * 1000
            + split_part(q2_time_str, '.', 2)::integer
        end,
        case when q1_time_str is not null and q1_time_str != '' then
            split_part(q1_time_str, ':', 1)::integer * 60000
            + split_part(split_part(q1_time_str, ':', 2), '.', 1)::integer * 1000
            + split_part(q1_time_str, '.', 2)::integer
        end
    ) as best_time_ms,
    _ingested_at
from flattened
