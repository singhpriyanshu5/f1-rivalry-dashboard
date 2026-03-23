---
title: F1 Teammate Rivalry Dashboard
hide_title: true
---

```sql seasons
select distinct season from snowflake.mart_qualifying_h2h order by season desc
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

```sql sprint_filtered
select * from snowflake.mart_sprint_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
order by round
```

```sql sprint_stats
select
    count(case when sprint_winner_code = driver_1_code then 1 end) as d1_sprint_wins,
    count(case when sprint_winner_code = driver_2_code then 1 end) as d2_sprint_wins,
    min(driver_1_code) as d1_code,
    min(driver_2_code) as d2_code,
    sum(driver_1_points) as d1_sprint_points,
    sum(driver_2_points) as d2_sprint_points,
    count(*) as sprint_rounds
from snowflake.mart_sprint_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
```

```sql sprint_points_by_round
select
    round_label,
    driver_code,
    points
from (
    select round, round_label, driver_1_code as driver_code, driver_1_points as points
    from snowflake.mart_sprint_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
    union all
    select round, round_label, driver_2_code as driver_code, driver_2_points as points
    from snowflake.mart_sprint_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
)
order by round, driver_code
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

```sql quali_coverage
select
    (select count(distinct round) from snowflake.mart_race_h2h
     where season = ${inputs.season.value}
       and constructor_id = '${inputs.constructor.value}'
       and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}') as total_race_rounds,
    (select count(*) from snowflake.mart_qualifying_h2h
     where season = ${inputs.season.value}
       and constructor_id = '${inputs.constructor.value}'
       and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
       and both_set_time = true) as quali_compared_rounds
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
    <div class="f1-hero-badge">Analytics Dashboard</div>
    <div class="f1-hero-title">FORMULA <span>1</span></div>
    <div class="f1-hero-subtitle">TEAMMATE RIVALRY</div>
    <div class="f1-hero-sub">The only fair comparison in F1 — same car, same strategy options, same machinery. Select a season and constructor to compare teammates head-to-head.</div>
</div>

<div class="f1-controls">

<Dropdown
    name=season
    data={seasons}
    value=season
    defaultValue={2026}
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

```sql narrative
select narrative_text, model_id, generated_at
from snowflake.mart_season_narrative
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
limit 1
```

{#if narrative.length > 0}

<div class="f1-narrative-card">
    <div class="f1-narrative-badge">AI Season Story</div>
    <div class="f1-narrative-text">{@html narrative[0].narrative_text}</div>
    <div class="f1-narrative-meta">Based on {race_filtered.length} rounds of {inputs.season.value} season data · Powered by {narrative[0].model_id}</div>
</div>

{/if}

<nav class="f1-section-nav">
    <a href="#section-qualifying" class="f1-nav-pill red">Quali</a>
    <a href="#section-race" class="f1-nav-pill teal">Race</a>
    {#if sprint_filtered.length > 0}<a href="#section-sprint" class="f1-nav-pill yellow">Sprint</a>{/if}
    <a href="#section-points" class="f1-nav-pill blue">Points</a>
    <a href="#section-grid" class="f1-nav-pill green">Grid vs Finish</a>
    <a href="#section-pitstops" class="f1-nav-pill purple">Pit Stops</a>
    <a href="#section-reliability" class="f1-nav-pill amber">Reliability</a>
    <a href="#section-pace-consistency" class="f1-nav-pill cyan">Consistency</a>
    <a href="#section-pace" class="f1-nav-pill orange">Lap Pace</a>
</nav>

```sql season_summary
select * from snowflake.mart_season_summary
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
```

<div class="f1-scorecard">
    <div class="f1-scorecard-title">Season Verdict</div>
    <div class="f1-verdict-grid">
        <div class="f1-verdict-card {season_summary[0].quali_verdict === season_summary[0].driver_1_code ? 'winner-d1' : season_summary[0].quali_verdict === season_summary[0].driver_2_code ? 'winner-d2' : 'winner-tie'}">
            <div class="f1-verdict-label">Qualifying</div>
            <div class="f1-verdict-winner">{season_summary[0].quali_verdict}</div>
            <div class="f1-verdict-detail">{season_summary[0].d1_quali_wins} – {season_summary[0].d2_quali_wins}</div>
        </div>
        <div class="f1-verdict-card {season_summary[0].race_verdict === season_summary[0].driver_1_code ? 'winner-d1' : season_summary[0].race_verdict === season_summary[0].driver_2_code ? 'winner-d2' : 'winner-tie'}">
            <div class="f1-verdict-label">Race H2H</div>
            <div class="f1-verdict-winner">{season_summary[0].race_verdict}</div>
            <div class="f1-verdict-detail">{season_summary[0].d1_race_wins} – {season_summary[0].d2_race_wins}</div>
        </div>
        <div class="f1-verdict-card {season_summary[0].points_verdict === season_summary[0].driver_1_code ? 'winner-d1' : season_summary[0].points_verdict === season_summary[0].driver_2_code ? 'winner-d2' : 'winner-tie'}">
            <div class="f1-verdict-label">Points</div>
            <div class="f1-verdict-winner">{season_summary[0].points_verdict}</div>
            <div class="f1-verdict-detail">{season_summary[0].d1_total_points} – {season_summary[0].d2_total_points}</div>
        </div>
        <div class="f1-verdict-card {season_summary[0].reliability_verdict === season_summary[0].driver_1_code ? 'winner-d1' : season_summary[0].reliability_verdict === season_summary[0].driver_2_code ? 'winner-d2' : 'winner-tie'}">
            <div class="f1-verdict-label">Reliability</div>
            <div class="f1-verdict-winner">{season_summary[0].reliability_verdict}</div>
            <div class="f1-verdict-detail">{season_summary[0].d1_dnfs} – {season_summary[0].d2_dnfs} DNFs</div>
        </div>
        <div class="f1-verdict-card {season_summary[0].pit_verdict === season_summary[0].driver_1_code ? 'winner-d1' : season_summary[0].pit_verdict === season_summary[0].driver_2_code ? 'winner-d2' : 'winner-tie'}">
            <div class="f1-verdict-label">Pit Stops</div>
            <div class="f1-verdict-winner">{season_summary[0].pit_verdict}</div>
            <div class="f1-verdict-detail">{season_summary[0].d1_avg_pit}s – {season_summary[0].d2_avg_pit}s avg</div>
        </div>
        {#if season_summary[0].sprint_rounds > 0}
        <div class="f1-verdict-card {season_summary[0].sprint_race_verdict === season_summary[0].driver_1_code ? 'winner-d1' : season_summary[0].sprint_race_verdict === season_summary[0].driver_2_code ? 'winner-d2' : 'winner-tie'}">
            <div class="f1-verdict-label">Sprint Race</div>
            <div class="f1-verdict-winner">{season_summary[0].sprint_race_verdict}</div>
            <div class="f1-verdict-detail">{season_summary[0].d1_sprint_wins} – {season_summary[0].d2_sprint_wins}</div>
        </div>
        <div class="f1-verdict-card {season_summary[0].sprint_quali_verdict === season_summary[0].driver_1_code ? 'winner-d1' : season_summary[0].sprint_quali_verdict === season_summary[0].driver_2_code ? 'winner-d2' : 'winner-tie'}">
            <div class="f1-verdict-label">Sprint Quali</div>
            <div class="f1-verdict-winner">{season_summary[0].sprint_quali_verdict}</div>
            <div class="f1-verdict-detail">{season_summary[0].d1_sprint_quali_wins} – {season_summary[0].d2_sprint_quali_wins}</div>
        </div>
        {/if}
    </div>
</div>

<div class="f1-section" id="section-qualifying">
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

{#if quali_coverage[0].quali_compared_rounds < quali_coverage[0].total_race_rounds}
<div class="f1-chart-note">Showing {quali_coverage[0].quali_compared_rounds} of {quali_coverage[0].total_race_rounds} rounds — {quali_coverage[0].total_race_rounds - quali_coverage[0].quali_compared_rounds} excluded (teammate did not set a qualifying time).</div>
{/if}

</div>
</div>

<div class="f1-section teal" id="section-race">
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

{#if sprint_filtered.length > 0}

<div class="f1-section yellow" id="section-sprint">
    <div class="f1-section-title">Sprint Battle</div>
    <div class="f1-section-subtitle">Sprint weekends add another dimension to the rivalry — shorter races, fewer laps, no pit stops.</div>
    <div class="f1-stats-row">
        <div class="f1-stat-card accent-red">

<BigValue
    data={sprint_stats}
    value=d1_sprint_wins
    title="{sprint_stats[0].d1_code} Sprint H2H"
/>

</div>
        <div class="f1-stat-card accent-teal">

<BigValue
    data={sprint_stats}
    value=d2_sprint_wins
    title="{sprint_stats[0].d2_code} Sprint H2H"
/>

</div>
        <div class="f1-stat-card accent-red">

<BigValue
    data={sprint_stats}
    value=d1_sprint_points
    title="{sprint_stats[0].d1_code} Sprint Points"
/>

</div>
        <div class="f1-stat-card accent-teal">

<BigValue
    data={sprint_stats}
    value=d2_sprint_points
    title="{sprint_stats[0].d2_code} Sprint Points"
/>

</div>
    </div>
    <div class="f1-chart-wrap">

<BarChart
    data={sprint_points_by_round}
    x=round_label
    y=points
    series=driver_code
    seriesColors={{ [sprint_stats[0].d1_code]: '#E10600', [sprint_stats[0].d2_code]: '#00D2BE' }}
    sort=false
    title="Sprint Points Per Round"
    yAxisTitle="Points"
    xAxisTitle="Round"
    labels=true
    type=grouped
/>

</div>
    <div class="f1-chart-wrap f1-detail-table">
        <div class="f1-chart-label">Sprint Round-by-Round Detail</div>

<DataTable
    data={sprint_filtered}
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
    <Column id=sprint_winner_code title="Winner" />
</DataTable>

</div>
</div>

{/if}

<div class="f1-section blue" id="section-points">
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

<div class="f1-chart-note">Includes sprint race points where applicable.</div>
</div>
</div>

```sql places_gained_by_driver
select round_label, driver_code, places_gained from (
    select
        round,
        round_label,
        driver_1_code as driver_code,
        driver_1_grid - driver_1_finish as places_gained
    from snowflake.mart_race_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
      and driver_1_grid > 0 and driver_2_grid > 0
      and driver_1_finish > 0 and driver_2_finish > 0

    union all

    select
        round,
        round_label,
        driver_2_code as driver_code,
        driver_2_grid - driver_2_finish as places_gained
    from snowflake.mart_race_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
      and driver_1_grid > 0 and driver_2_grid > 0
      and driver_1_finish > 0 and driver_2_finish > 0
)
order by round, driver_code
```

```sql places_gained_stats
select
    min(driver_1_code) as d1_code,
    min(driver_2_code) as d2_code,
    round(avg(driver_1_grid - driver_1_finish), 1) as d1_avg_places,
    round(avg(driver_2_grid - driver_2_finish), 1) as d2_avg_places,
    max(driver_1_grid - driver_1_finish) as d1_best_recovery,
    max(driver_2_grid - driver_2_finish) as d2_best_recovery
from snowflake.mart_race_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
  and driver_1_grid > 0 and driver_2_grid > 0
  and driver_1_finish > 0 and driver_2_finish > 0
```

```sql places_gained_cumulative
select round, round_label, driver_code, cumulative_places_gained from (
    select
        round,
        round_label,
        driver_1_code as driver_code,
        1 as driver_order,
        sum(driver_1_grid - driver_1_finish)
            over (order by round rows unbounded preceding) as cumulative_places_gained
    from snowflake.mart_race_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
      and driver_1_grid > 0 and driver_2_grid > 0
      and driver_1_finish > 0 and driver_2_finish > 0

    union all

    select
        round,
        round_label,
        driver_2_code as driver_code,
        2 as driver_order,
        sum(driver_2_grid - driver_2_finish)
            over (order by round rows unbounded preceding) as cumulative_places_gained
    from snowflake.mart_race_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
      and driver_1_grid > 0 and driver_2_grid > 0
      and driver_1_finish > 0 and driver_2_finish > 0
)
order by round, driver_order
```

<div class="f1-section green" id="section-grid">
    <div class="f1-section-title">Grid vs Finish — Places Gained</div>
    <div class="f1-section-subtitle">Who makes up places on race day? Positive = finished ahead of grid position.</div>
    <div class="f1-stats-row">
        <div class="f1-stat-card accent-red">

<BigValue
    data={places_gained_stats}
    value=d1_avg_places
    title="{places_gained_stats[0].d1_code} Avg Places Gained"
/>

</div>
        <div class="f1-stat-card accent-teal">

<BigValue
    data={places_gained_stats}
    value=d2_avg_places
    title="{places_gained_stats[0].d2_code} Avg Places Gained"
/>

</div>
        <div class="f1-stat-card accent-red">

<BigValue
    data={places_gained_stats}
    value=d1_best_recovery
    title="{places_gained_stats[0].d1_code} Best Recovery"
/>

</div>
        <div class="f1-stat-card accent-teal">

<BigValue
    data={places_gained_stats}
    value=d2_best_recovery
    title="{places_gained_stats[0].d2_code} Best Recovery"
/>

</div>
    </div>
    <div class="f1-chart-wrap">

<BarChart
    data={places_gained_by_driver}
    x=round_label
    y=places_gained
    series=driver_code
    seriesColors={{ [race_stats[0].d1_code]: '#E10600', [race_stats[0].d2_code]: '#00D2BE' }}
    sort=false
    title="Places Gained Per Round — Positive = Gained Positions, Negative = Lost Positions"
    yAxisTitle="Places Gained"
    xAxisTitle="Round"
    labels=true
    type=grouped
>
    <ReferenceLine y=0 />
</BarChart>

</div>
    <div class="f1-chart-wrap">

<LineChart
    data={places_gained_cumulative}
    x=round_label
    y=cumulative_places_gained
    series=driver_code
    seriesColors={{ [race_stats[0].d1_code]: '#E10600', [race_stats[0].d2_code]: '#00D2BE' }}
    sort=false
    title="Cumulative Places Gained Over Season — Higher = Better Race Day Converter"
    xAxisTitle="Round"
    yAxisTitle="Total Places Gained"
/>

</div>
</div>

```sql pit_filtered
select * from snowflake.mart_pit_stop_h2h
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
order by round, driver_1_stop_number
```

```sql pit_stats
select
    d1_code,
    d2_code,
    round(avg(driver_1_pit_duration_s), 2) as d1_avg_pit,
    round(avg(driver_2_pit_duration_s), 2) as d2_avg_pit,
    count(case when pitted_first_code = d1_code then 1 end) as d1_pitted_first,
    count(case when pitted_first_code = d2_code then 1 end) as d2_pitted_first
from snowflake.mart_pit_stop_h2h,
     (select split_part('${inputs.pairing.value}', '|', 1) as d1_code,
             split_part('${inputs.pairing.value}', '|', 2) as d2_code) codes
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
group by d1_code, d2_code
```

```sql pit_duration_by_round
select
    round_label,
    driver_code,
    pit_duration_s,
    stop_number
from (
    select round_label, round, driver_1_code as driver_code, driver_1_pit_duration_s as pit_duration_s, driver_1_stop_number as stop_number
    from snowflake.mart_pit_stop_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
    union all
    select round_label, round, driver_2_code as driver_code, driver_2_pit_duration_s as pit_duration_s, driver_2_stop_number as stop_number
    from snowflake.mart_pit_stop_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
)
order by round, stop_number, driver_code
```

```sql pit_lap_scatter
select
    round_label,
    driver_code,
    lap_number,
    stop_number
from (
    select round_label, round, driver_1_code as driver_code, driver_1_lap as lap_number, driver_1_stop_number as stop_number
    from snowflake.mart_pit_stop_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
    union all
    select round_label, round, driver_2_code as driver_code, driver_2_lap as lap_number, driver_2_stop_number as stop_number
    from snowflake.mart_pit_stop_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
)
order by round, stop_number
```

<div class="f1-section purple" id="section-pitstops">
    <div class="f1-section-title">Pit Stop Strategy Battle</div>
    <div class="f1-section-subtitle">Undercut or overcut? Who the team pits first and who gets the faster stop.</div>
    <div class="f1-stats-row">
        <div class="f1-stat-card accent-red">

<BigValue
    data={pit_stats}
    value=d1_avg_pit
    title="{pit_stats[0].d1_code} Avg Pit (s)"
/>

</div>
        <div class="f1-stat-card accent-teal">

<BigValue
    data={pit_stats}
    value=d2_avg_pit
    title="{pit_stats[0].d2_code} Avg Pit (s)"
/>

</div>
        <div class="f1-stat-card accent-red">

<BigValue
    data={pit_stats}
    value=d1_pitted_first
    title="{pit_stats[0].d1_code} Pitted First"
/>

</div>
        <div class="f1-stat-card accent-teal">

<BigValue
    data={pit_stats}
    value=d2_pitted_first
    title="{pit_stats[0].d2_code} Pitted First"
/>

</div>
    </div>
    <div class="f1-chart-wrap">

<BarChart
    data={pit_duration_by_round}
    x=round_label
    y=pit_duration_s
    series=driver_code
    seriesColors={{ [race_stats[0].d1_code]: '#E10600', [race_stats[0].d2_code]: '#00D2BE' }}
    sort=false
    title="Pit Stop Duration by Round (seconds)"
    yAxisTitle="Duration (s)"
    xAxisTitle="Round"
    type=grouped
/>

</div>
    <div class="f1-chart-wrap">

<ScatterPlot
    data={pit_lap_scatter}
    x=round_label
    y=lap_number
    series=driver_code
    seriesColors={{ [race_stats[0].d1_code]: '#E10600', [race_stats[0].d2_code]: '#00D2BE' }}
    sort=false
    title="Pit Stop Lap Timing — Who Gets Pitted First Each Round"
    yAxisTitle="Lap Number"
    xAxisTitle="Round"
    pointSize=10
/>

</div>
</div>

```sql reliability_stats
select
    d1_code,
    d2_code,
    total_rounds,
    d1_dnfs,
    d2_dnfs,
    round(100.0 * (total_rounds - d1_dnfs) / total_rounds, 0) as d1_reliability_pct,
    round(100.0 * (total_rounds - d2_dnfs) / total_rounds, 0) as d2_reliability_pct,
    d1_mechanical,
    d2_mechanical
from (
    select
        min(driver_1_code) as d1_code,
        min(driver_2_code) as d2_code,
        count(*) as total_rounds,
        count(case when driver_1_dnf_category != 'finished' then 1 end) as d1_dnfs,
        count(case when driver_2_dnf_category != 'finished' then 1 end) as d2_dnfs,
        count(case when driver_1_dnf_category = 'mechanical' then 1 end) as d1_mechanical,
        count(case when driver_2_dnf_category = 'mechanical' then 1 end) as d2_mechanical
    from snowflake.mart_race_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
)
```

```sql dnf_by_category
select driver_code, dnf_category, count(*) as dnf_count from (
    select driver_1_code as driver_code, driver_1_dnf_category as dnf_category
    from snowflake.mart_race_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
      and driver_1_dnf_category != 'finished'
    union all
    select driver_2_code as driver_code, driver_2_dnf_category as dnf_category
    from snowflake.mart_race_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
      and driver_2_dnf_category != 'finished'
)
group by driver_code, dnf_category
order by driver_code, dnf_category
```

```sql dnf_log
select
    round,
    round_label as race,
    driver_code,
    status,
    dnf_category,
    teammate_points
from (
    select round, round_label, driver_1_code as driver_code, driver_1_status as status,
           driver_1_dnf_category as dnf_category, driver_2_points as teammate_points
    from snowflake.mart_race_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
      and driver_1_dnf_category != 'finished'
    union all
    select round, round_label, driver_2_code as driver_code, driver_2_status as status,
           driver_2_dnf_category as dnf_category, driver_1_points as teammate_points
    from snowflake.mart_race_h2h
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'
      and driver_2_dnf_category != 'finished'
)
order by round
```

<div class="f1-section amber" id="section-reliability">
    <div class="f1-section-title">DNF & Reliability Tracker</div>
    <div class="f1-section-subtitle">Reliability decides championships. Who kept the car running and what it cost when they didn't.</div>
    <div class="f1-stats-row">
        <div class="f1-stat-card accent-red">

<BigValue
    data={reliability_stats}
    value=d1_reliability_pct
    title="{reliability_stats[0].d1_code} Reliability %"
    fmt='#,##0"%"'
/>

</div>
        <div class="f1-stat-card accent-teal">

<BigValue
    data={reliability_stats}
    value=d2_reliability_pct
    title="{reliability_stats[0].d2_code} Reliability %"
    fmt='#,##0"%"'
/>

</div>
        <div class="f1-stat-card accent-red">

<BigValue
    data={reliability_stats}
    value=d1_mechanical
    title="{reliability_stats[0].d1_code} Mechanical DNFs"
/>

</div>
        <div class="f1-stat-card accent-teal">

<BigValue
    data={reliability_stats}
    value=d2_mechanical
    title="{reliability_stats[0].d2_code} Mechanical DNFs"
/>

</div>
    </div>

{#if dnf_by_category.length > 0}

<div class="f1-chart-wrap">

<BarChart
    data={dnf_by_category}
    x=driver_code
    y=dnf_count
    series=dnf_category
    sort=false
    title="DNFs by Category"
    yAxisTitle="Count"
    type=stacked
/>

</div>
    <div class="f1-chart-wrap f1-detail-table">
        <div class="f1-chart-label">DNF Log — Points Left on the Table</div>

<DataTable
    data={dnf_log}
    rows=8
>
    <Column id=round title="Rd" />
    <Column id=race title="Race" />
    <Column id=driver_code title="Driver" />
    <Column id=status title="Status" />
    <Column id=dnf_category title="Category" />
    <Column id=teammate_points title="Teammate Scored" />
</DataTable>

</div>

{:else}

<div class="f1-chart-note">No DNFs recorded for this pairing — both drivers finished every race.</div>

{/if}

</div>

```sql pace_summary
select * from snowflake.mart_lap_pace_summary
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and driver_code in (split_part('${inputs.pairing.value}', '|', 1), split_part('${inputs.pairing.value}', '|', 2))
order by round, driver_code
```

```sql pace_consistency_stats
select
    d1.d1_code,
    d2.d2_code,
    d1.d1_avg_consistency,
    d2.d2_avg_consistency,
    d1.d1_avg_stddev,
    d2.d2_avg_stddev
from (
    select
        driver_code as d1_code,
        round(avg(consistency_score), 1) as d1_avg_consistency,
        round(avg(stddev_lap_s), 3) as d1_avg_stddev
    from snowflake.mart_lap_pace_summary
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_code = split_part('${inputs.pairing.value}', '|', 1)
    group by driver_code
) d1
cross join (
    select
        driver_code as d2_code,
        round(avg(consistency_score), 1) as d2_avg_consistency,
        round(avg(stddev_lap_s), 3) as d2_avg_stddev
    from snowflake.mart_lap_pace_summary
    where season = ${inputs.season.value}
      and constructor_id = '${inputs.constructor.value}'
      and driver_code = split_part('${inputs.pairing.value}', '|', 2)
    group by driver_code
) d2
```

```sql pace_spread_by_round
select
    round_label,
    driver_code,
    iqr_s,
    median_lap_s,
    fastest_lap_s,
    p25_lap_s,
    p75_lap_s
from snowflake.mart_lap_pace_summary
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and driver_code in (split_part('${inputs.pairing.value}', '|', 1), split_part('${inputs.pairing.value}', '|', 2))
order by round, driver_code
```

```sql pace_consistency_by_round
select
    round_label,
    driver_code,
    consistency_score,
    stddev_lap_s,
    iqr_s
from snowflake.mart_lap_pace_summary
where season = ${inputs.season.value}
  and constructor_id = '${inputs.constructor.value}'
  and driver_code in (split_part('${inputs.pairing.value}', '|', 1), split_part('${inputs.pairing.value}', '|', 2))
order by round, driver_code
```

<div class="f1-section cyan" id="section-pace-consistency">
    <div class="f1-section-title">Lap Pace Consistency</div>
    <div class="f1-section-subtitle">Who keeps a tighter window? Season-wide pace variation and consistency scoring per driver.</div>
    <div class="f1-stats-row">
        <div class="f1-stat-card accent-red">

<BigValue
    data={pace_consistency_stats}
    value=d1_avg_consistency
    title="{pace_consistency_stats[0].d1_code} Consistency Score"
/>

</div>
        <div class="f1-stat-card accent-teal">

<BigValue
    data={pace_consistency_stats}
    value=d2_avg_consistency
    title="{pace_consistency_stats[0].d2_code} Consistency Score"
/>

</div>
        <div class="f1-stat-card accent-red">

<BigValue
    data={pace_consistency_stats}
    value=d1_avg_stddev
    title="{pace_consistency_stats[0].d1_code} Avg Stddev (s)"
/>

</div>
        <div class="f1-stat-card accent-teal">

<BigValue
    data={pace_consistency_stats}
    value=d2_avg_stddev
    title="{pace_consistency_stats[0].d2_code} Avg Stddev (s)"
/>

</div>
    </div>
    <div class="f1-chart-wrap">

<BarChart
    data={pace_spread_by_round}
    x=round_label
    y=iqr_s
    series=driver_code
    seriesColors={{ [race_stats[0].d1_code]: '#E10600', [race_stats[0].d2_code]: '#00D2BE' }}
    sort=false
    title="Pace Window Per Round (IQR) — Smaller Bar = Tighter, More Consistent Pace"
    yAxisTitle="Interquartile Range (s)"
    xAxisTitle="Round"
    type=grouped
    labels=true
/>

</div>
    <div class="f1-chart-wrap">

<LineChart
    data={pace_consistency_by_round}
    x=round_label
    y=consistency_score
    series=driver_code
    seriesColors={{ [race_stats[0].d1_code]: '#E10600', [race_stats[0].d2_code]: '#00D2BE' }}
    sort=false
    title="Consistency Score by Round — Higher = More Consistent"
    yAxisTitle="Consistency Score (0–100)"
    xAxisTitle="Round"
/>

</div>
    <div class="f1-chart-note">
        <strong>How Consistency Score works:</strong> Based on the IQR-to-median ratio — the interquartile range (middle 50% of lap times) divided by the median lap time. A smaller ratio means tighter pace.
        Scored 0–100 where 100 = perfectly uniform pace, 0 = highly erratic. Safety car and outlier laps are excluded. The bar chart shows the raw IQR in seconds per round — a smaller bar means the driver kept their middle-50% lap times in a narrower window.
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

<div class="f1-section orange" id="section-pace">
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
