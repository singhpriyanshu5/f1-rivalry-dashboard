-- Race head-to-head: teammate comparison on race results
-- Includes DNF categories from dim_dnf_status

with driver_starts as (
    select
        season,
        constructor_id,
        driver_id,
        count(*) as num_starts
    from {{ ref('stg_results') }}
    group by 1, 2, 3
),

ranked as (
    select *,
        row_number() over (
            partition by season, constructor_id
            order by num_starts desc, driver_id
        ) as rn
    from driver_starts
),

primary_drivers as (
    select season, constructor_id, driver_id
    from ranked
    where rn <= 2
),

results_filtered as (
    select r.*
    from {{ ref('stg_results') }} r
    inner join primary_drivers pd
        on r.season = pd.season
        and r.constructor_id = pd.constructor_id
        and r.driver_id = pd.driver_id
),

results_with_dnf as (
    select
        r.*,
        coalesce(d.category, 'finished') as dnf_category
    from results_filtered r
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
    *,
    case
        when driver_1_finish < driver_2_finish then driver_1_code
        when driver_2_finish < driver_1_finish then driver_2_code
        -- If both DNF, compare laps completed
        when driver_1_laps > driver_2_laps then driver_1_code
        when driver_2_laps > driver_1_laps then driver_2_code
        else 'TIE'
    end as race_winner_code,
    driver_1_finish - driver_1_grid as driver_1_places_gained,
    driver_2_finish - driver_2_grid as driver_2_places_gained
from teammate_pairs
