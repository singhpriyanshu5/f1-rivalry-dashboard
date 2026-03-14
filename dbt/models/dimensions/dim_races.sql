-- Race dimension: season, round, location label for use in charts

select
    season,
    round,
    race_name,
    locality,
    country,
    circuit_name,
    race_date,
    'R' || lpad(round::varchar, 2, '0') || ' ' || locality as round_label
from {{ ref('stg_schedule') }}
