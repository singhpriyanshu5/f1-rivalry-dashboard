---
title: F1 Teammate Rivalry Dashboard
hide_title: true
---

```sql seasons
select distinct season from snowflake.mart_qualifying_h2h order by season
```

```sql constructors
select distinct constructor_id, constructor_name
from snowflake.mart_qualifying_h2h
where season = ${inputs.season.value}
order by constructor_name
```

```sql quali_filtered
select * from snowflake.mart_qualifying_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
order by round
```

```sql race_filtered
select * from snowflake.mart_race_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
order by round
```

```sql points_filtered
select * from snowflake.mart_points_trajectory
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
order by round
```

```sql quali_stats
select
    count(*) as total_rounds,
    count(case when faster_driver_code = driver_1_code then 1 end) as d1_quali_wins,
    count(case when faster_driver_code = driver_2_code then 1 end) as d2_quali_wins,
    min(driver_1_code) as d1_code,
    min(driver_2_code) as d2_code,
    round(avg(abs(gap_ms)), 0) as avg_gap_ms
from snowflake.mart_qualifying_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and both_set_time = true
```

```sql race_stats
select
    count(case when race_winner_code = driver_1_code then 1 end) as d1_race_wins,
    count(case when race_winner_code = driver_2_code then 1 end) as d2_race_wins,
    min(driver_1_code) as d1_code,
    min(driver_2_code) as d2_code,
    sum(driver_1_points) as d1_total_points,
    sum(driver_2_points) as d2_total_points
from snowflake.mart_race_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
```

```sql quali_delta
select
    round,
    abs(gap_ms) as gap_abs_ms,
    faster_driver_code,
    driver_1_code || ' (' || driver_1_time_ms || ' ms)' as d1_label,
    driver_2_code || ' (' || driver_2_time_ms || ' ms)' as d2_label,
    gap_ms
from snowflake.mart_qualifying_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and both_set_time = true
order by round
```

```sql race_wins_by_driver
select driver_code, count(*) as wins
from (
    select race_winner_code as driver_code
    from snowflake.mart_race_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and race_winner_code != 'TIE'
)
group by driver_code
order by wins desc
```

```sql quali_wins_by_driver
select driver_code, count(*) as wins
from (
    select faster_driver_code as driver_code
    from snowflake.mart_qualifying_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and faster_driver_code != 'TIE'
      and both_set_time = true
)
group by driver_code
order by wins desc
```

```sql race_points_swing
select round, points_swing, driver_1_code, driver_2_code, points_leader
from (
    select
        round,
        driver_1_points - driver_2_points as points_swing,
        driver_1_code,
        driver_2_code,
        case
            when driver_1_points > driver_2_points then driver_1_code
            when driver_2_points > driver_1_points then driver_2_code
            else 'Even'
        end as points_leader,
        case
            when driver_1_points > driver_2_points then 1
            when driver_2_points > driver_1_points then 2
            else 3
        end as sort_priority
    from snowflake.mart_race_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
)
where points_swing != 0
order by sort_priority, round
```

```sql race_position_gap
select
    round,
    driver_2_finish - driver_1_finish as position_gap,
    race_winner_code as "H2H Winner",
    driver_1_code,
    driver_2_code,
    'H2H Winner: ' || race_winner_code || ' (P' ||
    case
        when race_winner_code = driver_1_code then cast(cast(driver_1_finish as int) as varchar)
        when race_winner_code = driver_2_code then cast(cast(driver_2_finish as int) as varchar)
        else cast(cast(driver_1_finish as int) as varchar)
    end || ')' as winner_label
from snowflake.mart_race_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
order by round
```

```sql race_h2h_cumulative
select round, driver_code, cumulative_wins from (
    select
        round,
        driver_1_code as driver_code,
        1 as driver_order,
        sum(case when race_winner_code = driver_1_code then 1 else 0 end)
            over (order by round rows unbounded preceding) as cumulative_wins
    from snowflake.mart_race_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'

    union all

    select
        round,
        driver_2_code as driver_code,
        2 as driver_order,
        sum(case when race_winner_code = driver_2_code then 1 else 0 end)
            over (order by round rows unbounded preceding) as cumulative_wins
    from snowflake.mart_race_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
)
order by round, driver_order
```

<div class="f1-hero">
    <div class="f1-hero-badge">Formula 1 Analytics</div>
    <div class="f1-hero-title">TEAMMATE <span>RIVALRY</span></div>
    <div class="f1-hero-sub">The only fair comparison in F1 — same car, same strategy options, same machinery. Select a season and constructor to compare teammates head-to-head.</div>
</div>

<div class="f1-controls">

<Dropdown
    name=season
    data={seasons}
    value=season
    defaultValue={2024}
    title="Season"
/>

<Dropdown
    name=constructor
    data={constructors}
    value=constructor_id
    label=constructor_name
    defaultValue="red_bull"
    title="Constructor"
/>

</div>

<div class="f1-section">
    <div class="f1-section-title">Qualifying Battle</div>
    <div class="f1-section-subtitle">Who puts it on pole? Best qualifying time comparison across rounds.</div>
    <div class="f1-stats-row">
        <div class="f1-stat-card accent-red">

<BigValue
    data={quali_stats}
    value=d1_quali_wins
    title="{quali_stats[0].d1_code} Quali Wins"
/>

</div>
        <div class="f1-stat-card accent-teal">

<BigValue
    data={quali_stats}
    value=d2_quali_wins
    title="{quali_stats[0].d2_code} Quali Wins"
/>

</div>
        <div class="f1-stat-card">

<BigValue
    data={quali_stats}
    value=avg_gap_ms
    title="Avg Gap (ms)"
/>

</div>
    </div>
    <div class="f1-chart-wrap">

<BarChart
    data={quali_delta}
    x=round
    y=gap_abs_ms
    series=faster_driver_code
    title="Qualifying Gap (ms) — Bigger Bar = Larger Margin"
    yAxisTitle="Gap (ms)"
    xAxisTitle="Round"
    labels=true
    type=stacked
/>

</div>
</div>

<div class="f1-section teal">
    <div class="f1-section-title">Race Battle</div>
    <div class="f1-section-subtitle">Sunday is what counts. Head-to-head race finishes and points scored.</div>
    <div class="f1-stats-row">
        <div class="f1-stat-card accent-red">

<BigValue
    data={race_stats}
    value=d1_race_wins
    title="{race_stats[0].d1_code} Race H2H Wins"
/>

</div>
        <div class="f1-stat-card accent-teal">

<BigValue
    data={race_stats}
    value=d2_race_wins
    title="{race_stats[0].d2_code} Race H2H Wins"
/>

</div>
        <div class="f1-stat-card accent-red">

<BigValue
    data={race_stats}
    value=d1_total_points
    title="{race_stats[0].d1_code} Points"
/>

</div>
        <div class="f1-stat-card accent-teal">

<BigValue
    data={race_stats}
    value=d2_total_points
    title="{race_stats[0].d2_code} Points"
/>

</div>
    </div>
    <div class="f1-chart-wrap">

<BarChart
    data={race_points_swing}
    x=round
    y=points_swing
    series=points_leader
    title="Points Swing Per Round — Bars Above Zero = {race_points_swing[0].driver_1_code} Scored More"
    yAxisTitle="Points Advantage"
    xAxisTitle="Round"
    labels=true
    type=stacked
>
    <ReferenceLine y=0 />
</BarChart>

</div>
    <div class="f1-chart-wrap">

<ScatterPlot
    data={race_position_gap}
    x=round
    y=position_gap
    series="H2H Winner"
    tooltipTitle=winner_label
    title="Finish Position Gap — Above Zero = {race_position_gap[0].driver_1_code} Ahead"
    yAxisTitle="Position Gap"
    xAxisTitle="Round"
    pointSize=10
>
    <ReferenceLine y=0 label="Even" />
</ScatterPlot>

</div>
    <div class="f1-chart-wrap">

<LineChart
    data={race_h2h_cumulative}
    x=round
    y=cumulative_wins
    series=driver_code
    title="Head-to-Head Race Wins — Running Score"
    yAxisTitle="Cumulative Wins"
    xAxisTitle="Round"
/>

</div>
    <div class="f1-chart-wrap f1-detail-table">
        <div class="f1-chart-label">Round-by-Round Detail</div>

<DataTable
    data={race_filtered}
    rows=8
>
    <Column id=round title="Rd" />
    <Column id=driver_1_code title="Driver 1" />
    <Column id=driver_1_grid title="Grid" />
    <Column id=driver_1_finish title="Finish" />
    <Column id=driver_1_points title="Pts" />
    <Column id=driver_2_code title="Driver 2" />
    <Column id=driver_2_grid title="Grid" />
    <Column id=driver_2_finish title="Finish" />
    <Column id=driver_2_points title="Pts" />
    <Column id=race_winner_code title="Winner" />
</DataTable>

</div>
</div>

<div class="f1-section blue">
    <div class="f1-section-title">Points Trajectory</div>
    <div class="f1-section-subtitle">Championship points accumulation — teammate comparison across the season.</div>
    <div class="f1-chart-wrap">

<LineChart
    data={points_filtered}
    x=round
    y=cumulative_points
    series=driver_code
    title="Championship Points — Teammate Comparison"
    xAxisTitle="Round"
    yAxisTitle="Cumulative Points"
/>

</div>
</div>

<div class="f1-section orange">
    <div class="f1-section-title">Lap Pace Comparison</div>
    <div class="f1-section-subtitle">Lap-by-lap pace comparison between teammates. Safety car laps filtered out.</div>

```sql rounds_available
select distinct round from snowflake.mart_race_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
order by round
```

<div class="f1-inline-control">

<Dropdown
    name=pace_round
    data={rounds_available}
    value=round
    defaultValue={1}
    title="Select Round"
/>

</div>

```sql lap_pace_filtered
select * from snowflake.mart_lap_pace
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and round = ${inputs.pace_round.value}
order by lap_number
```

<div class="f1-chart-wrap">

<LineChart
    data={lap_pace_filtered}
    x=lap_number
    y=lap_time_s
    series=driver_code
    title="Lap-by-Lap Pace — Teammate Comparison (Round {inputs.pace_round.value})"
    xAxisTitle="Lap Number"
    yAxisTitle="Lap Time (seconds)"
/>

</div>
</div>
