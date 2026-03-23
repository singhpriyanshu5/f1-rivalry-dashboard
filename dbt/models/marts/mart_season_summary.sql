-- Season summary scorecard: one row per pairing with all H2H verdicts
-- Aggregates qualifying, race, points, reliability, and pit stop stats

with quali as (
    select
        season,
        constructor_id,
        driver_1_code,
        driver_2_code,
        count(case when faster_driver_code = driver_1_code then 1 end) as d1_quali_wins,
        count(case when faster_driver_code = driver_2_code then 1 end) as d2_quali_wins
    from {{ ref('mart_qualifying_h2h') }}
    where both_set_time = true
    group by season, constructor_id, driver_1_code, driver_2_code
),

race as (
    select
        season,
        constructor_id,
        driver_1_code,
        driver_2_code,
        count(case when race_winner_code = driver_1_code then 1 end) as d1_race_wins,
        count(case when race_winner_code = driver_2_code then 1 end) as d2_race_wins,
        sum(driver_1_points) as d1_total_points,
        sum(driver_2_points) as d2_total_points,
        count(*) as total_rounds,
        count(case when driver_1_dnf_category != 'finished' then 1 end) as d1_dnfs,
        count(case when driver_2_dnf_category != 'finished' then 1 end) as d2_dnfs
    from {{ ref('mart_race_h2h') }}
    group by season, constructor_id, driver_1_code, driver_2_code
),

pits as (
    select
        season,
        constructor_id,
        driver_1_code,
        driver_2_code,
        round(avg(driver_1_pit_duration_s), 2) as d1_avg_pit,
        round(avg(driver_2_pit_duration_s), 2) as d2_avg_pit
    from {{ ref('mart_pit_stop_h2h') }}
    group by season, constructor_id, driver_1_code, driver_2_code
),

sprint as (
    select
        season,
        constructor_id,
        driver_1_code,
        driver_2_code,
        count(case when sprint_winner_code = driver_1_code then 1 end) as d1_sprint_wins,
        count(case when sprint_winner_code = driver_2_code then 1 end) as d2_sprint_wins,
        count(case when driver_1_grid < driver_2_grid then 1 end) as d1_sprint_quali_wins,
        count(case when driver_2_grid < driver_1_grid then 1 end) as d2_sprint_quali_wins,
        sum(driver_1_points) as d1_sprint_points,
        sum(driver_2_points) as d2_sprint_points,
        count(*) as sprint_rounds
    from {{ ref('mart_sprint_h2h') }}
    group by season, constructor_id, driver_1_code, driver_2_code
)

select
    r.season,
    r.constructor_id,
    r.driver_1_code,
    r.driver_2_code,

    -- Qualifying verdict
    coalesce(q.d1_quali_wins, 0) as d1_quali_wins,
    coalesce(q.d2_quali_wins, 0) as d2_quali_wins,
    case
        when coalesce(q.d1_quali_wins, 0) > coalesce(q.d2_quali_wins, 0) then r.driver_1_code
        when coalesce(q.d2_quali_wins, 0) > coalesce(q.d1_quali_wins, 0) then r.driver_2_code
        else 'TIE'
    end as quali_verdict,

    -- Race verdict
    r.d1_race_wins,
    r.d2_race_wins,
    case
        when r.d1_race_wins > r.d2_race_wins then r.driver_1_code
        when r.d2_race_wins > r.d1_race_wins then r.driver_2_code
        else 'TIE'
    end as race_verdict,

    -- Points verdict
    r.d1_total_points,
    r.d2_total_points,
    case
        when r.d1_total_points > r.d2_total_points then r.driver_1_code
        when r.d2_total_points > r.d1_total_points then r.driver_2_code
        else 'TIE'
    end as points_verdict,

    -- Reliability verdict
    r.total_rounds,
    r.d1_dnfs,
    r.d2_dnfs,
    case
        when r.d1_dnfs < r.d2_dnfs then r.driver_1_code
        when r.d2_dnfs < r.d1_dnfs then r.driver_2_code
        else 'TIE'
    end as reliability_verdict,

    -- Pit stop verdict
    coalesce(p.d1_avg_pit, 0) as d1_avg_pit,
    coalesce(p.d2_avg_pit, 0) as d2_avg_pit,
    case
        when coalesce(p.d1_avg_pit, 0) > 0 and coalesce(p.d2_avg_pit, 0) > 0
             and p.d1_avg_pit < p.d2_avg_pit then r.driver_1_code
        when coalesce(p.d1_avg_pit, 0) > 0 and coalesce(p.d2_avg_pit, 0) > 0
             and p.d2_avg_pit < p.d1_avg_pit then r.driver_2_code
        else 'TIE'
    end as pit_verdict,

    -- Sprint race verdict
    coalesce(s.d1_sprint_wins, 0) as d1_sprint_wins,
    coalesce(s.d2_sprint_wins, 0) as d2_sprint_wins,
    coalesce(s.d1_sprint_points, 0) as d1_sprint_points,
    coalesce(s.d2_sprint_points, 0) as d2_sprint_points,
    coalesce(s.sprint_rounds, 0) as sprint_rounds,
    case
        when coalesce(s.d1_sprint_wins, 0) > coalesce(s.d2_sprint_wins, 0) then r.driver_1_code
        when coalesce(s.d2_sprint_wins, 0) > coalesce(s.d1_sprint_wins, 0) then r.driver_2_code
        else 'TIE'
    end as sprint_race_verdict,

    -- Sprint qualifying verdict
    coalesce(s.d1_sprint_quali_wins, 0) as d1_sprint_quali_wins,
    coalesce(s.d2_sprint_quali_wins, 0) as d2_sprint_quali_wins,
    case
        when coalesce(s.d1_sprint_quali_wins, 0) > coalesce(s.d2_sprint_quali_wins, 0) then r.driver_1_code
        when coalesce(s.d2_sprint_quali_wins, 0) > coalesce(s.d1_sprint_quali_wins, 0) then r.driver_2_code
        else 'TIE'
    end as sprint_quali_verdict

from race r
left join quali q
    on r.season = q.season
    and r.constructor_id = q.constructor_id
    and r.driver_1_code = q.driver_1_code
    and r.driver_2_code = q.driver_2_code
left join pits p
    on r.season = p.season
    and r.constructor_id = p.constructor_id
    and r.driver_1_code = p.driver_1_code
    and r.driver_2_code = p.driver_2_code
left join sprint s
    on r.season = s.season
    and r.constructor_id = s.constructor_id
    and r.driver_1_code = s.driver_1_code
    and r.driver_2_code = s.driver_2_code
