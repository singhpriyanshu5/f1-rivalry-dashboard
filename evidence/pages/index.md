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

```sql pairings
select distinct
    driver_1_code || '|' || driver_2_code as pairing_value,
    driver_1_code || ' vs ' || driver_2_code as pairing_label
from snowflake.mart_race_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
order by pairing_label
```

```sql quali_filtered
select * from snowflake.mart_qualifying_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
order by round
```

```sql race_filtered
select * from snowflake.mart_race_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
order by round
```

```sql points_filtered
select * from snowflake.mart_points_trajectory
where season = ${inputs.season.value}
  and driver_code in (split_part('${inputs.pairing.value}', '|', 1), split_part('${inputs.pairing.value}', '|', 2))
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
  and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
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
  and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
```

```sql quali_delta
select
    round,
    round_label,
    abs(gap_ms) as gap_abs_ms,
    faster_driver_code,
    driver_1_code || ' (' || driver_1_time_ms || ' ms)' as d1_label,
    driver_2_code || ' (' || driver_2_time_ms || ' ms)' as d2_label,
    gap_ms
from snowflake.mart_qualifying_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
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
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
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
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
      and faster_driver_code != 'TIE'
      and both_set_time = true
)
group by driver_code
order by wins desc
```

```sql race_points_swing
select round, round_label, points_swing, driver_1_code, driver_2_code, points_leader
from (
    select
        round,
        round_label,
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
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
)
where points_swing != 0
order by round
```

```sql race_position_gap
select
    round,
    round_label,
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
  and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
order by round
```

```sql race_h2h_cumulative
select round, round_label, driver_code, cumulative_wins from (
    select
        round,
        round_label,
        driver_1_code as driver_code,
        1 as driver_order,
        sum(case when race_winner_code = driver_1_code then 1 else 0 end)
            over (order by round rows unbounded preceding) as cumulative_wins
    from snowflake.mart_race_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'

    union all

    select
        round,
        round_label,
        driver_2_code as driver_code,
        2 as driver_order,
        sum(case when race_winner_code = driver_2_code then 1 else 0 end)
            over (order by round rows unbounded preceding) as cumulative_wins
    from snowflake.mart_race_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
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

<Dropdown
    name=pairing
    data={pairings}
    value=pairing_value
    label=pairing_label
    title="Driver Pairing"
/>

</div>

<div class="f1-driver-legend">
    <span class="f1-driver-chip red">{race_filtered[0].driver_1_code}</span> <span class="f1-driver-fullname">{race_filtered[0].driver_1_name}</span>
    <span class="f1-driver-vs">vs</span>
    <span class="f1-driver-chip teal">{race_filtered[0].driver_2_code}</span> <span class="f1-driver-fullname">{race_filtered[0].driver_2_name}</span>
</div>

<div class="f1-section">
    <div class="f1-section-title">Qualifying Battle</div>
    <div class="f1-section-subtitle">Who puts it on pole? Best qualifying time comparison across rounds.</div>
    <div class="f1-stats-row">
        <div class="f1-stat-card accent-red">

<BigValue
    data={quali_stats}
    value=d1_quali_wins
    title="{quali_stats[0].d1_code} Quali Head-to-Head"
/>

</div>
        <div class="f1-stat-card accent-teal">

<BigValue
    data={quali_stats}
    value=d2_quali_wins
    title="{quali_stats[0].d2_code} Quali Head-to-Head"
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
    x=round_label
    y=gap_abs_ms
    series=faster_driver_code
    seriesColors={{ [race_stats[0].d1_code]: '#E10600', [race_stats[0].d2_code]: '#00D2BE' }}
    sort=false
    title="Quali Head-to-Head - Gap (ms), Bigger Bar = Larger Margin"
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
    title="{race_stats[0].d1_code} Race Head-to-Head"
/>

</div>
        <div class="f1-stat-card accent-teal">

<BigValue
    data={race_stats}
    value=d2_race_wins
    title="{race_stats[0].d2_code} Race Head-to-Head"
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
    x=round_label
    y=points_swing
    series=points_leader
    seriesColors={{ [race_stats[0].d1_code]: '#E10600', [race_stats[0].d2_code]: '#00D2BE' }}
    sort=false
    title="Points Swing Per Round - Bars Above Zero = {race_points_swing[0].driver_1_code} Scored More"
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
    x=round_label
    y=position_gap
    series="H2H Winner"
    seriesColors={{ [race_stats[0].d1_code]: '#E10600', [race_stats[0].d2_code]: '#00D2BE' }}
    sort=false
    tooltipTitle=winner_label
    title="Finish Position Gap - Above Zero = {race_position_gap[0].driver_1_code} Ahead"
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
    x=round_label
    y=cumulative_wins
    series=driver_code
    seriesColors={{ [race_stats[0].d1_code]: '#E10600', [race_stats[0].d2_code]: '#00D2BE' }}
    sort=false
    title="Race Head-to-Head - Running Score"
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
    <Column id=locality title="Race" />
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
    x=round_label
    y=cumulative_points
    series=driver_code
    seriesColors={{ [race_stats[0].d1_code]: '#E10600', [race_stats[0].d2_code]: '#00D2BE' }}
    sort=false
    title="Championship Points - Teammate Comparison"
    xAxisTitle="Round"
    yAxisTitle="Cumulative Points"
/>

</div>
</div>

```sql race_time_gap
select
    round,
    round_label,
    d1_code,
    d2_code,
    d1_total_time,
    d2_total_time,
    round(d2_total_time - d1_total_time, 3) as time_gap_s,
    case
        when d1_total_time < d2_total_time then d1_code
        when d2_total_time < d1_total_time then d2_code
        else 'Even'
    end as faster_driver
from (
    select
        p1.round,
        p1.round_label,
        p1.driver_code as d1_code,
        p2.driver_code as d2_code,
        sum(p1.lap_time_s) as d1_total_time,
        sum(p2.lap_time_s) as d2_total_time
    from snowflake.mart_lap_pace p1
    inner join snowflake.mart_lap_pace p2
        on p1.season = p2.season
        and p1.round = p2.round
        and p1.lap_number = p2.lap_number
        and p1.constructor_id = p2.constructor_id
        and p1.driver_code != p2.driver_code
    where p1.season = ${inputs.season.value}
      and p1.constructor_id = '${inputs.constructor.value}'
      and p1.driver_code = split_part('${inputs.pairing.value}', '|', 1)
      and p2.driver_code = split_part('${inputs.pairing.value}', '|', 2)
    group by p1.round, p1.round_label, p1.driver_code, p2.driver_code
)
where d1_total_time > 0 and d2_total_time > 0
order by round
```

<div class="f1-section orange">
    <div class="f1-section-title">Lap Pace Comparison</div>
    <div class="f1-section-subtitle">Lap-by-lap pace comparison between teammates. Safety car laps filtered out.</div>

    <div class="f1-chart-wrap">

<BarChart
    data={race_time_gap}
    x=round_label
    y=time_gap_s
    series=faster_driver
    seriesColors={{ [race_stats[0].d1_code]: '#E10600', [race_stats[0].d2_code]: '#00D2BE' }}
    sort=false
    title="Total Race Time Gap (seconds) - Positive = {race_time_gap[0].d1_code} Faster"
    yAxisTitle="Time Gap (s)"
    xAxisTitle="Round"
    labels=true
    type=stacked
>
    <ReferenceLine y=0 />
</BarChart>

<div class="f1-chart-note">DNF rounds compare only laps both drivers completed. Safety car laps filtered.</div>
</div>

```sql rounds_available
select distinct round, round_label from snowflake.mart_race_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
order by round
```

<div class="f1-inline-control">

<Dropdown
    name=pace_round
    data={rounds_available}
    value=round
    label=round_label
    defaultValue={1}
    title="Select Round"
/>

</div>

```sql lap_pace_filtered
select * from snowflake.mart_lap_pace
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and round = ${inputs.pace_round.value}
  and driver_code in (split_part('${inputs.pairing.value}', '|', 1), split_part('${inputs.pairing.value}', '|', 2))
order by lap_number
```

<div class="f1-chart-wrap">

<LineChart
    data={lap_pace_filtered}
    x=lap_number
    y=lap_time_s
    series=driver_code
    seriesColors={{ [race_stats[0].d1_code]: '#E10600', [race_stats[0].d2_code]: '#00D2BE' }}
    sort=false
    title="Lap-by-Lap Pace - Teammate Comparison ({lap_pace_filtered[0].round_label})"
    xAxisTitle="Lap Number"
    yAxisTitle="Lap Time (seconds)"
/>

</div>
</div>
