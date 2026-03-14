-- Qualifying head-to-head: self-join teammates on (season, round, constructor_id)
-- Pairs whoever actually qualified together per round (handles mid-season driver swaps)

with teammate_pairs as (
    select
        a.season,
        a.round,
        a.constructor_id,
        a.constructor_name,
        a.driver_id as driver_1_id,
        a.driver_code as driver_1_code,
        a.driver_name as driver_1_name,
        a.best_time_ms as driver_1_time_ms,
        a.position as driver_1_pos,
        b.driver_id as driver_2_id,
        b.driver_code as driver_2_code,
        b.driver_name as driver_2_name,
        b.best_time_ms as driver_2_time_ms,
        b.position as driver_2_pos
    from {{ ref('stg_qualifying') }} a
    inner join {{ ref('stg_qualifying') }} b
        on a.season = b.season
        and a.round = b.round
        and a.constructor_id = b.constructor_id
        and a.driver_id < b.driver_id  -- avoid duplicates + self-join
)

select
    tp.season,
    tp.round,
    tp.constructor_id,
    tp.constructor_name,
    tp.driver_1_id,
    tp.driver_1_code,
    tp.driver_1_name,
    tp.driver_1_time_ms,
    tp.driver_1_pos,
    tp.driver_2_id,
    tp.driver_2_code,
    tp.driver_2_name,
    tp.driver_2_time_ms,
    tp.driver_2_pos,
    dr.round_label,
    dr.locality,
    tp.driver_1_time_ms - tp.driver_2_time_ms as gap_ms,
    case
        when tp.driver_1_time_ms < tp.driver_2_time_ms then tp.driver_1_code
        when tp.driver_2_time_ms < tp.driver_1_time_ms then tp.driver_2_code
        else 'TIE'
    end as faster_driver_code,
    case
        when tp.driver_1_time_ms is null or tp.driver_2_time_ms is null then false
        else true
    end as both_set_time
from teammate_pairs tp
left join {{ ref('dim_races') }} dr
    on tp.season = dr.season and tp.round = dr.round
