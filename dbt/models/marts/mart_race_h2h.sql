-- Race head-to-head: teammate comparison on race results
-- Pairs whoever actually raced together per round (handles mid-season driver swaps)
-- Includes DNF categories from dim_dnf_status

with results_with_dnf as (
    select
        r.*,
        coalesce(d.category, 'finished') as dnf_category
    from {{ ref('stg_results') }} r
    left join {{ ref('dim_dnf_status') }} d
        on r.status = d.status
),

teammate_pairs as (
    select
        a.season,
        a.round,
        a.constructor_id,
        a.constructor_name,
        a.driver_id as driver_1_id,
        a.driver_code as driver_1_code,
        a.driver_name as driver_1_name,
        a.grid_position as driver_1_grid,
        a.finish_position as driver_1_finish,
        a.points as driver_1_points,
        a.status as driver_1_status,
        a.dnf_category as driver_1_dnf_category,
        a.laps_completed as driver_1_laps,
        b.driver_id as driver_2_id,
        b.driver_code as driver_2_code,
        b.driver_name as driver_2_name,
        b.grid_position as driver_2_grid,
        b.finish_position as driver_2_finish,
        b.points as driver_2_points,
        b.status as driver_2_status,
        b.dnf_category as driver_2_dnf_category,
        b.laps_completed as driver_2_laps
    from results_with_dnf a
    inner join results_with_dnf b
        on a.season = b.season
        and a.round = b.round
        and a.constructor_id = b.constructor_id
        and a.driver_id < b.driver_id
)

select
    tp.*,
    dr.round_label,
    dr.locality,
    case
        when tp.driver_1_finish < tp.driver_2_finish then tp.driver_1_code
        when tp.driver_2_finish < tp.driver_1_finish then tp.driver_2_code
        when tp.driver_1_laps > tp.driver_2_laps then tp.driver_1_code
        when tp.driver_2_laps > tp.driver_1_laps then tp.driver_2_code
        else 'TIE'
    end as race_winner_code,
    tp.driver_1_finish - tp.driver_1_grid as driver_1_places_gained,
    tp.driver_2_finish - tp.driver_2_grid as driver_2_places_gained
from teammate_pairs tp
left join {{ ref('dim_races') }} dr
    on tp.season = dr.season and tp.round = dr.round
