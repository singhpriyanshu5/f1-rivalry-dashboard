with raw as (
    select
        season,
        round,
        raw_data,
        _ingested_at
    from {{ source('raw', 'raw_sprint_results') }}
),

flattened as (
    select
        r.season,
        r.round,
        f.value:Driver:driverId::varchar as driver_id,
        f.value:Driver:code::varchar as driver_code,
        f.value:Driver:givenName::varchar || ' ' || f.value:Driver:familyName::varchar as driver_name,
        f.value:Constructor:constructorId::varchar as constructor_id,
        f.value:Constructor:name::varchar as constructor_name,
        f.value:grid::integer as grid_position,
        f.value:position::integer as finish_position,
        f.value:points::float as points,
        f.value:status::varchar as status,
        f.value:laps::integer as laps_completed,
        r._ingested_at
    from raw r,
    lateral flatten(input => r.raw_data) f
)

select * from flattened
