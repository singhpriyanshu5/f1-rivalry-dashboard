-- Cumulative points per driver per round from standings data

select
    season,
    round,
    driver_id,
    driver_code,
    driver_name,
    constructor_id,
    standings_position,
    cumulative_points,
    wins
from {{ ref('stg_driver_standings') }}
