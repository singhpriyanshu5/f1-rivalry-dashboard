-- Cumulative points per driver per round from standings data

select
    s.season,
    s.round,
    s.driver_id,
    s.driver_code,
    s.driver_name,
    s.constructor_id,
    s.standings_position,
    s.cumulative_points,
    s.wins,
    dr.round_label,
    dr.locality
from {{ ref('stg_driver_standings') }} s
left join {{ ref('dim_races') }} dr
    on s.season = dr.season and s.round = dr.round
