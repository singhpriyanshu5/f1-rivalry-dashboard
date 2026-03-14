-- Qualifying head-to-head: self-join teammates on (season, round, constructor_id)
-- Filters to the 2 drivers with most starts per constructor/season to handle mid-season swaps.

with driver_starts as (
    select
        season,
        constructor_id,
        driver_id,
        count(*) as num_starts
    from {{ ref('stg_qualifying') }}
    group by 1, 2, 3
),

-- Rank drivers by starts within each constructor/season, keep top 2
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

qualifying_filtered as (
    select q.*
    from {{ ref('stg_qualifying') }} q
    inner join primary_drivers pd
        on q.season = pd.season
        and q.constructor_id = pd.constructor_id
        and q.driver_id = pd.driver_id
),

-- Self-join to pair teammates per round
teammate_pairs as (
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
    from qualifying_filtered a
    inner join qualifying_filtered b
        on a.season = b.season
        and a.round = b.round
        and a.constructor_id = b.constructor_id
        and a.driver_id < b.driver_id  -- avoid duplicates + self-join
)

select
    season,
    round,
    constructor_id,
    constructor_name,
    driver_1_id,
    driver_1_code,
    driver_1_name,
    driver_1_time_ms,
    driver_1_pos,
    driver_2_id,
    driver_2_code,
    driver_2_name,
    driver_2_time_ms,
    driver_2_pos,
    -- Gap in ms (positive = driver_1 slower)
    driver_1_time_ms - driver_2_time_ms as gap_ms,
    -- Who was faster
    case
        when driver_1_time_ms < driver_2_time_ms then driver_1_code
        when driver_2_time_ms < driver_1_time_ms then driver_2_code
        else 'TIE'
    end as faster_driver_code,
    case
        when driver_1_time_ms is null or driver_2_time_ms is null then false
        else true
    end as both_set_time
from teammate_pairs
