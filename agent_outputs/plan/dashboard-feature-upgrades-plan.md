# F1 Rivalry Dashboard — Feature Upgrades Plan

## Context
The dashboard is fully deployed and running (3 seasons, 50 rounds, automated Airflow pipeline). The goal is to add high-impact features that improve analytical depth and make for a compelling YouTube demo. Key insight: **several data sources are already collected but never visualized** (pit stops, places gained, DNF categories).

---

## Recommended Features (ranked by impact/effort ratio)

### 1. Pit Stop Strategy Battle (SMALL effort, HIGH impact)
**Why:** Pit stop data is collected but completely unused. Undercut/overcut strategy is a huge F1 fan talking point.

- **New dbt mart:** `mart_pit_stop_h2h.sql` — self-join `stg_pit_stops` via `stg_results` for constructor context, pair teammates per round
- **New Evidence source:** `evidence/sources/snowflake/mart_pit_stop_h2h.sql`
- **New section in `index.md`** (purple accent):
  - Stat cards: Avg pit duration per driver, "Pitted First" count
  - BarChart: pit duration per driver per round
  - ScatterPlot: pit lap number per driver (shows who team pits first)
- **Files:** `dbt/models/marts/mart_pit_stop_h2h.sql`, `evidence/pages/index.md`, `evidence/pages/+layout.svelte`

### 2. Grid vs Finish — Places Gained/Lost (SMALL effort, HIGH impact)
**Why:** `mart_race_h2h` already computes `places_gained` columns but they're never shown. Answers "who's the better racer vs qualifier?"

- **No dbt changes** — data already exists in `mart_race_h2h`
- **New queries + charts in `index.md`:**
  - Diverging BarChart: places gained/lost per round per driver
  - Stat cards: Avg places gained, Best recovery drive
  - LineChart: cumulative places gained over season
- **Files:** `evidence/pages/index.md`

### 3. DNF & Reliability Tracker (SMALL-MEDIUM effort, HIGH impact)
**Why:** `dim_dnf_status` categorizes every DNF, `mart_race_h2h` has `dnf_category` — none visualized. Reliability decides championships.

- **Optional mart:** `mart_reliability_h2h.sql` (or pure Evidence SQL)
  - DNF count by category per driver, reliability %, "points lost" estimate (teammate's score when you DNF)
- **New section in `index.md`:**
  - Stat cards: Reliability %, Mechanical DNFs
  - Stacked BarChart: DNF categories per driver
  - DataTable: DNF log with round, status, what teammate scored
- **Files:** `dbt/models/marts/mart_reliability_h2h.sql` (optional), `evidence/pages/index.md`

### 4. Season Summary Scorecard (MEDIUM effort, HIGH visual impact)
**Why:** No at-a-glance verdict currently. A single-frame summary is critical for YouTube thumbnails and shareability.

- **New mart:** `mart_season_summary.sql` — aggregates all H2H stats into one row per pairing
- **New top-of-page section** (after driver legend, before Qualifying):
  - Grid of verdict cards: Quali Winner, Race Winner, Points Leader, Faster Pit Crew, More Consistent, More Reliable
  - Each card color-coded to winning driver (red/teal)
- **Files:** `dbt/models/marts/mart_season_summary.sql`, `evidence/pages/index.md`

### 5. Lap Pace Consistency (MEDIUM effort, MEDIUM impact)
**Why:** Current lap pace section only shows one round at a time. An aggregate view answers "who is more consistent?"

- **New mart:** `mart_lap_pace_summary.sql` — median, stddev, P25/P75 per driver per round
- **New visualization:**
  - ScatterPlot: all laps plotted (x=round, y=lap_time), creating pace "clouds"
  - Stat cards: Consistency Score (inverse stddev)
- **Files:** `dbt/models/marts/mart_lap_pace_summary.sql`, `evidence/pages/index.md`

---

## Implementation Order

| Phase | Feature | Why first |
|-------|---------|-----------|
| A | Pit Stop Battle + Places Gained | Both use existing unused data, zero/minimal dbt work |
| B | DNF Tracker + Season Scorecard | Scorecard depends on having all sections built |
| C | Lap Pace Consistency | Stretch goal, most complex visualization |

## Key Files to Modify
- `dbt/models/marts/` — new mart SQL files (pit stops, reliability, summary, pace summary)
- `dbt/models/sources.yml` or `schema.yml` — register new models + tests
- `evidence/sources/snowflake/` — new source queries for any new marts
- `evidence/pages/index.md` — new sections, queries, charts
- `evidence/pages/+layout.svelte` — new accent color classes (purple, green)

## Verification
- `dbt run && dbt test` — all models build, all tests pass
- `cd evidence && npm run sources && npm run dev` — preview dashboard locally
- Test with multiple pairings (esp. mid-season swap like 2025 Red Bull LAW→VER)
- Verify all new sections filter correctly via cascading dropdowns
