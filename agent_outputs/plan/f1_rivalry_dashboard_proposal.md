# F1 Teammate Performance Dashboard — Project Plan

## Problem Statement

In Formula 1, the only truly fair performance comparison is between teammates — same car, same equipment, same opportunities. Yet most fans rely on headline championship standings to judge a driver's season, which obscures the real story: *when* did a driver start losing the intra-team battle, *why* (pace, reliability, race craft, tire management?), and *how much did it cost them in points?*

This dashboard surfaces the full teammate rivalry story for any constructor across a selected season — moving beyond simple standings to show qualifying pace gaps, race execution, DNF cost, and tire management, all driven by a fully automated data pipeline and published as a static website anyone can visit with no login required.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Ingestion | Python (FastF1 + requests) |
| Orchestration | Apache Airflow |
| Raw / Bronze Storage | AWS S3 (partitioned by season/round) |
| Data Warehouse | Snowflake |
| Transformation | dbt (SQL) |
| Dashboard | Evidence.dev (static site, SQL + Markdown) |
| Deployment | GitHub Pages (via GitHub Actions) |
| Infrastructure | Docker (local dev), Airflow on MWAA or self-hosted |

### Why Evidence.dev over Preset.io

Preset requires every viewer to have an account — a significant friction point for sharing a YouTube project with a general audience. Evidence.dev compiles your dashboard to a fully static site deployed on GitHub Pages: shareable as a plain URL, no login, no account, works on any device. It also keeps SQL as the primary language (queries run directly against your Snowflake dbt marts), which fits naturally into the DE stack and is a talking point in itself — "BI as code" is a concept worth introducing to both fresh grads and senior engineers.

---

## Upstream Data Sources

### 1. Jolpica-F1 API
**Base URL:** `http://api.jolpi.ca/ergast/f1/`
**Auth:** None required
**Rate limit:** 200 requests/hour (unauthenticated)

| Endpoint | Data Pulled | Grain |
|---|---|---|
| `/{season}/{round}/qualifying.json` | Q1/Q2/Q3 times per driver | Round |
| `/{season}/{round}/results.json` | Finish position, grid position, points, DNF status | Round |
| `/{season}/driverStandings/{round}.json` | Cumulative championship points after each round | Round |
| `/{season}/drivers.json` | Driver metadata (name, nationality, DOB) | Season |
| `/{season}/constructors.json` | Constructor metadata | Season |

### 2. OpenF1 API
**Base URL:** `https://api.openf1.org/v1/`
**Auth:** None required
**Rate limit:** No hard limit documented — implement polite throttling

| Endpoint | Data Pulled | Grain |
|---|---|---|
| `/sessions?year=&session_name=Race` | Session keys needed to query lap/stint endpoints | Session |
| `/laps?session_key=&driver_number=` | Lap-by-lap times per driver per session | Lap |
| `/pit?session_key=` | Pit stop lap number, stop duration | Stop |
| `/stints?session_key=` | Tire compound, stint start/end lap | Stint |

---

## Data Model (Medallion Architecture in Snowflake)

```
Bronze (raw)          Silver (cleaned)           Gold (marts)
─────────────────     ──────────────────────     ──────────────────────────
raw_qualifying    →   stg_qualifying         →   mart_qualifying_h2h
raw_results       →   stg_results            →   mart_race_h2h
raw_standings     →   stg_driver_standings   →   mart_points_trajectory
raw_laps          →   stg_laps               →   mart_stint_pace
raw_stints        →   stg_stints             →
raw_pit_stops     →   stg_pit_stops          →
                      dim_drivers
                      dim_constructors
                      dim_sessions
                      dim_dnf_status          ← classifies 100+ Jolpica
                                                 status codes into:
                                                 mechanical / crash /
                                                 finished / other
```

**Key modeling challenge:** Jolpica operates at round-level grain; OpenF1 operates at lap-level grain. `dim_sessions` acts as the bridge, mapping `(season, round, session_type)` to OpenF1 `session_key` values.

---

## Key Metrics & Dashboard Widgets

### Widget 1 — Head-to-Head Scorecard (KPI Tiles)
Top-of-dashboard summary cards for the selected season and constructor pairing.
- Qualifying H2H record (e.g., 14–7)
- Race finish H2H record (when both drivers finished)
- Average qualifying gap in milliseconds
- Points gap at season end

*Evidence.dev component:* `<BigValue>` tiles — native, no custom code needed.

### Widget 2 — Qualifying Delta to Teammate, Season Arc (Line Chart)
X-axis: race round | Y-axis: gap in milliseconds vs. teammate
- Positive = faster than teammate, negative = slower
- Annotate inflection points (e.g., team upgrade packages, driver changes)
- **Insight surfaced:** Identifies exactly *when* in a season a driver's form shifted — not just whether they lost, but when and by how much

*Evidence.dev component:* `<LineChart>` with `referenceLine` annotations.

### Widget 3 — Grid vs. Finish Position Scatter (Scatter Plot)
One dot per race per driver. Diagonal reference line = neutral (started and finished same position).
- Above diagonal = positions gained, below = positions lost
- Color-coded by driver
- **Insight surfaced:** Separates qualifying performance from race execution — a driver can consistently out-qualify their teammate but lose ground in the race (and vice versa)

*Evidence.dev component:* `<ScatterPlot>` with `referenceLine` for the diagonal.

### Widget 4 — Points Left on Table — DNF Cost (Stacked Bar Chart)
Per driver per round: actual points earned vs. projected points based on running position at time of retirement.
- Stacked to split mechanical DNFs vs. driver-fault crashes (using `dim_dnf_status`)
- Cumulative season total shown as annotation
- **Insight surfaced:** Quantifies bad luck vs. driver error — one of the most debated topics in F1 punditry, answered with data

*Evidence.dev component:* `<BarChart>` with `type=stacked`.

### Widget 5 — Stint Pace Degradation (Line Chart)
Lap time per lap number within a tire stint, normalized to remove safety car laps and in/out laps.
- Both teammates on same compound plotted side by side per race
- Selectable by race round via Evidence.dev `<Dropdown>` filter
- **Insight surfaced:** Shows who manages tires better in long stints — often the hidden reason one teammate finishes stronger despite similar qualifying pace

*Evidence.dev component:* `<LineChart>` with `<Dropdown>` for round selection.

### Widget 6 — Championship Points Trajectory (Area Chart)
Cumulative points per round for both teammates across the season.
- Shaded area between the two lines highlights when and how fast the gap opened
- **Insight surfaced:** The "summary story" of the season in one view — anchors all the granular widgets into a narrative arc

*Evidence.dev component:* `<AreaChart>` with both drivers as series.

---

## How Evidence.dev Fits the Pipeline

Evidence queries your Snowflake gold marts directly at **build time** — it runs the SQL, bakes the results into the static site, and GitHub Actions pushes the compiled output to GitHub Pages. There is no live database connection in the published site; all data is embedded in the build.

```
Airflow DAG runs (post race weekend)
        │
        └── dbt_run completes (gold marts updated in Snowflake)
                │
                └── GitHub Actions trigger
                          │
                          ├── Evidence build (queries Snowflake marts)
                          ├── Compile static site
                          └── Deploy to GitHub Pages → public URL
```

This means the dashboard refresh cadence is tied to your Airflow pipeline — after each race weekend, a new build is triggered and the published site updates automatically. No manual steps, no Preset login, no shared credentials.

---

## Airflow DAG Structure (High Level)

```
Season/Round Trigger (weekly during season)
        │
        ├── fetch_jolpica_qualifying
        ├── fetch_jolpica_results
        ├── fetch_jolpica_standings
        ├── fetch_openf1_sessions       ← resolve session_keys first
        │         │
        │         ├── fetch_openf1_laps
        │         ├── fetch_openf1_stints
        │         └── fetch_openf1_pit_stops
        │
        ├── upload_to_s3_bronze
        ├── snowflake_copy_into_raw
        ├── dbt_run (staging → dims → marts)
        └── trigger_github_actions_build  ← kicks off Evidence build + Pages deploy
```

---

## Interesting Storylines This Dashboard Could Investigate

- **2023 Red Bull:** Verstappen vs. Pérez — when exactly did Pérez fall off and how much did reliability vs. pure pace contribute?
- **2022 Ferrari:** Leclerc vs. Sainz — Leclerc out-qualified Sainz almost every race but the points gap was much smaller. Why?
- **2016 Mercedes:** Hamilton vs. Rosberg — how many points did Hamilton's mechanical DNFs cost him, and did that decide the championship?
- **2024 McLaren:** Norris vs. Piastri — a genuinely close pairing mid-season. Who had the better tire management?

---

## YouTube Video Angle

**Target audience hook:** *"I built a shareable F1 rivalry dashboard — just send the link, no login needed — in half a day with AI"*

- Fresh grads see: a complete E2E pipeline from raw API → S3 → Snowflake → dbt → static website with real modeling decisions explained
- Senior DEs see: agentic coding handling the scaffolding while the engineer owns the architectural decisions (medallion layers, dim/fact design, DAG dependencies, Evidence-as-a-build-step)
- F1 fans see: genuinely interesting insights on current driver storylines, shareable as a plain URL with no friction
