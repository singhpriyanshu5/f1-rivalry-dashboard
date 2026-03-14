with raw as (
    select
        season,
        round,
        raw_data,
        _ingested_at
    from {{ source('raw', 'raw_driver_standings') }}
),

flattened as (
    select
        r.season,
        r.round,
        f.value:Driver:driverId::varchar as driver_id,
        f.value:Driver:code::varchar as driver_code,
        f.value:Driver:givenName::varchar || ' ' || f.value:Driver:familyName::varchar as driver_name,
        f.value:position::integer as standings_position,
        f.value:points::float as cumulative_points,
        f.value:wins::integer as wins,
        f.value:Constructors[0]:constructorId::varchar as constructor_id,
        r._ingested_at
    from raw r,
    lateral flatten(input => r.raw_data) f
)

select * from flattened
