# F1 Rivalry Dashboard — Feature Upgrades Implementation Summary

**Last updated:** 2026-03-20

---

## Completed Features

### Phase A — Completed

#### 1. Grid vs Finish — Places Gained/Lost (green section)
- **Data source:** Existing `mart_race_h2h` columns (`driver_1_places_gained`, `driver_2_places_gained`) — no dbt changes needed
- **Dashboard additions:**
  - 4 stat cards: Avg Places Gained + Best Recovery per driver
  - Grouped BarChart: places gained per round per driver (positive = gained positions)
  - LineChart: cumulative places gained over season
- **Files modified:** `evidence/pages/index.md`, `evidence/pages/+layout.svelte`

#### 2. Pit Stop Strategy Battle (purple section)
- **New dbt mart:** `dbt/models/marts/mart_pit_stop_h2h.sql` — joins `stg_pit_stops` with `stg_results`, pairs teammates per round by stop number, computes duration diff and who pitted first
- **New Evidence source:** `evidence/sources/snowflake/mart_pit_stop_h2h.sql`
- **Dashboard additions:**
  - 4 stat cards: Avg pit duration + "Pitted First" count per driver
  - Grouped BarChart: pit stop duration by round per driver
  - ScatterPlot: pit stop lap timing (who gets pitted first each round)
- **Files created:** `dbt/models/marts/mart_pit_stop_h2h.sql`, `evidence/sources/snowflake/mart_pit_stop_h2h.sql`
- **Files modified:** `evidence/pages/index.md`, `evidence/pages/+layout.svelte`, `dbt/models/marts/schema.yml`

### Phase B — Completed

#### 3. DNF & Reliability Tracker (amber section)
- **Data source:** Existing `mart_race_h2h` columns (`driver_1_dnf_category`, `driver_2_dnf_category`) — no dbt changes needed
- **Dashboard additions:**
  - 4 stat cards: Reliability % + Mechanical DNFs per driver
  - Stacked BarChart: DNFs by category (crash, mechanical, other) per driver
  - DataTable: DNF log with round, status, and teammate's points scored
  - Conditional rendering: shows "No DNFs" note when both drivers finished every race
- **Files modified:** `evidence/pages/index.md`, `evidence/pages/+layout.svelte`

#### 4. Season Summary Scorecard (top of page, below driver legend)
- **New dbt mart:** `dbt/models/marts/mart_season_summary.sql` — aggregates qualifying, race, points, reliability, and pit stop stats into one row per pairing with verdict columns
- **New Evidence source:** `evidence/sources/snowflake/mart_season_summary.sql`
- **Dashboard additions:**
  - 5 verdict cards in a grid: Qualifying, Race H2H, Points, Reliability, Pit Stops
  - Each card color-coded red/teal to the winning driver (grey for ties)
  - Score breakdown shown beneath each verdict
- **Files created:** `dbt/models/marts/mart_season_summary.sql`, `evidence/sources/snowflake/mart_season_summary.sql`
- **Files modified:** `evidence/pages/index.md`, `evidence/pages/+layout.svelte`, `dbt/models/marts/schema.yml`

### Other Improvements
- **Qualifying coverage note:** When rounds are excluded (teammate didn't set a qualifying time), a note appears: "Showing X of Y rounds — Z excluded"
- **New accent colors:** Green, purple, amber added to `+layout.svelte`
- **Animation delays:** Extended for new sections (6th–8th)

---

## Current Dashboard Section Order

1. Hero + Controls (season, constructor, pairing dropdowns)
2. Driver Legend (driver codes + full names)
3. **Section Navigation** *(sticky pill bar)*
4. **Season Verdict Scorecard**
5. Qualifying Battle (red accent)
6. Race Battle (teal accent)
7. Points Trajectory (blue accent)
8. Grid vs Finish — Places Gained (green accent)
9. Pit Stop Strategy Battle (purple accent)
10. DNF & Reliability Tracker (amber accent)
11. **Lap Pace Consistency** *(new, cyan accent)*
12. Lap Pace Comparison (orange accent)

---

## Current dbt Model Count

| Layer | Models |
|-------|--------|
| Staging | 6 (results, qualifying, laps, pit_stops, driver_standings, schedule) |
| Dimensions | 3 (drivers, constructors, dnf_status, races) |
| Marts | 7 (qualifying_h2h, race_h2h, points_trajectory, lap_pace, pit_stop_h2h, season_summary, **lap_pace_summary**) |
| **Total** | **17 models, 25 tests — all passing** |

---

### Phase C — Completed

#### 5. Lap Pace Consistency (cyan section)
- **New dbt mart:** `dbt/models/marts/mart_lap_pace_summary.sql` — median, stddev, P25/P75, IQR, consistency score per driver per round
- **New Evidence source:** `evidence/sources/snowflake/mart_lap_pace_summary.sql`
- **Dashboard additions:**
  - 4 stat cards: Consistency Score + Avg Stddev per driver
  - ScatterPlot: all laps plotted (x=round, y=lap_time) showing pace "clouds"
  - LineChart: consistency score by round per driver
- **Files created:** `dbt/models/marts/mart_lap_pace_summary.sql`, `evidence/sources/snowflake/mart_lap_pace_summary.sql`
- **Files modified:** `evidence/pages/index.md`, `evidence/pages/+layout.svelte`, `dbt/models/marts/schema.yml`

#### 6. Section Navigation (sticky pill bar)
- **Sticky navigation bar** below driver legend — stays visible on scroll
  - 8 color-coded pills matching each section's accent color
  - Smooth scroll with offset padding for sticky nav
  - Backdrop blur glass effect on the bar
  - All sections have anchor IDs for deep linking
- **Files modified:** `evidence/pages/index.md`, `evidence/pages/+layout.svelte`

---

## All Phases Complete

No remaining features in the upgrade plan.
