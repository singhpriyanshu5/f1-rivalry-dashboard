-- Flatten race schedule: one row per (season, round) with race name and location

with flattened as (
    select
        s.season,
        r.value:round::int as round,
        r.value:raceName::string as race_name,
        r.value:Circuit:circuitId::string as circuit_id,
        r.value:Circuit:circuitName::string as circuit_name,
        r.value:Circuit:Location:locality::string as locality,
        r.value:Circuit:Location:country::string as country,
        r.value:date::date as race_date
    from {{ source('raw', 'raw_schedule') }} s,
    lateral flatten(input => s.raw_data) r
)

select * from flattened
