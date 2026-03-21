-- Pit stop head-to-head: teammate comparison on pit stop strategy
-- Pairs teammates per round, compares stop count, duration, and lap timing

with pit_with_context as (
    select
        p.season,
        p.round,
        p.driver_id,
        r.driver_code,
        r.driver_name,
        r.constructor_id,
        r.constructor_name,
        p.stop_number,
        p.lap_number,
        p.pit_duration_s
    from {{ ref('stg_pit_stops') }} p
    inner join {{ ref('stg_results') }} r
        on p.season = r.season
        and p.round = r.round
        and p.driver_id = r.driver_id
    where p.pit_duration_s is not null
      and p.pit_duration_s < 120  -- filter out red flag / long stops
),

teammate_stops as (
    select
        a.season,
        a.round,
        a.constructor_id,
        a.constructor_name,
        a.driver_id as driver_1_id,
        a.driver_code as driver_1_code,
        a.driver_name as driver_1_name,
        a.stop_number as driver_1_stop_number,
        a.lap_number as driver_1_lap,
        a.pit_duration_s as driver_1_pit_duration_s,
        b.driver_id as driver_2_id,
        b.driver_code as driver_2_code,
        b.driver_name as driver_2_name,
        b.stop_number as driver_2_stop_number,
        b.lap_number as driver_2_lap,
        b.pit_duration_s as driver_2_pit_duration_s
    from pit_with_context a
    inner join pit_with_context b
        on a.season = b.season
        and a.round = b.round
        and a.constructor_id = b.constructor_id
        and a.stop_number = b.stop_number
        and a.driver_id < b.driver_id
)

select
    ts.*,
    dr.round_label,
    dr.locality,
    ts.driver_1_pit_duration_s - ts.driver_2_pit_duration_s as pit_duration_diff_s,
    case
        when ts.driver_1_lap < ts.driver_2_lap then ts.driver_1_code
        when ts.driver_2_lap < ts.driver_1_lap then ts.driver_2_code
        else 'SAME'
    end as pitted_first_code,
    case
        when ts.driver_1_pit_duration_s < ts.driver_2_pit_duration_s then ts.driver_1_code
        when ts.driver_2_pit_duration_s < ts.driver_1_pit_duration_s then ts.driver_2_code
        else 'TIE'
    end as faster_pit_code
from teammate_stops ts
left join {{ ref('dim_races') }} dr
    on ts.season = dr.season and ts.round = dr.round
