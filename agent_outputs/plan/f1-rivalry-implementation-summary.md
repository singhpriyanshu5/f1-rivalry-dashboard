# F1 Rivalry Dashboard — Implementation Summary

**Date:** 2026-03-14
**Status:** Full 2024 + 2025 seasons loaded (48 rounds total). Dashboard fully working with premium dark telemetry UI, race battle visualization upgrade (3 insight charts). dbt 12 models + 19 tests pass. Evidence build succeeds. Ready for deployment.

---

## What's Been Built

### Phase 0 — Project Scaffold & Infrastructure ✅

| Item | Path | Status |
|------|------|--------|
| Git repo initialized | `f1-rivalry-dashboard/` on `main` branch | Done |
| `.gitignore` | `.gitignore` | Done |
| `.env` / `.env.example` | `.env`, `.env.example` | Done — Snowflake creds, GitHub PAT, Evidence env vars |
| Snowflake setup | `sql/snowflake_setup.sql` | Done — executed, all raw tables created |
| API connectivity test | `scripts/test_apis.py` | Done — Jolpica 200 |
| Airflow Docker setup | `airflow/Dockerfile`, `airflow/docker-compose.yml` | Done — LocalExecutor, Postgres |
| Airflow requirements | `airflow/requirements.txt` | Done — snowflake-connector-python, requests, pandas |

**Decision: S3 layer skipped.** Data flows API → Snowflake directly.
**Decision: OpenF1 removed.** API now requires paid sponsorship + OAuth2. Replaced with Jolpica for laps and pit stops.

### Phase 1+2 — Ingestion (API → Snowflake) ✅

| Item | Path | Notes |
|------|------|-------|
| Jolpica client | `airflow/dags/utils/jolpica_client.py` | `fetch_qualifying`, `fetch_results`, `fetch_driver_standings`, `fetch_laps` (paginated), `fetch_pit_stops`, `fetch_schedule`. 0.5s delay, retry on 429. |
| OpenF1 client | `airflow/dags/utils/openf1_client.py` | **DEPRECATED** — OpenF1 requires paid auth since ~2025. Kept for reference. |
| Standalone ingestion script | `scripts/ingest_round.py` | Fully Jolpica-powered. 5 steps: qualifying, results, standings, laps, pit stops. Usage: `python scripts/ingest_round.py 2024 1` |
| Master DAG | `airflow/dags/f1_pipeline_dag.py` | Needs update to remove OpenF1 tasks |

**Data loading approach:**
- All tables: full API response array stored as one VARIANT row per (season, round). DELETE+INSERT for idempotency.
- All use temp table approach (VARCHAR → PARSE_JSON) per lessons learned.

**Raw Snowflake tables:**
- `RAW_QUALIFYING`, `RAW_RESULTS`, `RAW_DRIVER_STANDINGS` — Jolpica (original)
- `RAW_JOLPICA_LAPS` — Jolpica lap timing data (paginated, ~1000 entries per race)
- `RAW_JOLPICA_PIT_STOPS` — Jolpica pit stop data
- `RAW_LAPS`, `RAW_STINTS`, `RAW_SESSIONS`, `RAW_PIT_STOPS` — OpenF1 (deprecated, data from rounds 1-3 only)

**Data loaded:**
- 2024 Rounds 1–24: **all loaded** (all 5 tables per round)
- 2025 Rounds 1–24: **all loaded** (all 5 tables per round) — ingested 2026-03-14
- Initial parallel run hit Jolpica 429 rate limits; retried failed rounds sequentially — all succeeded
- **Important:** Parallel ingestion hits Jolpica 429 rate limits — must run rounds sequentially with 2s delay between rounds

### Phase 3 — dbt Transformations ✅

**All 12 models pass. All 19 tests pass.**

**Note on schema naming:** dbt prepends the default schema (`RAW`) to custom schemas, creating `RAW_STAGING` and `RAW_ANALYTICS`.

**Staging (views → RAW_STAGING schema):**

| Model | Key Logic |
|-------|-----------|
| `stg_qualifying` | Parses "M:SS.mmm" → milliseconds. Handles empty string Q times. `best_time_ms = COALESCE(q3, q2, q1)`. Flattens VARIANT array via LATERAL FLATTEN. |
| `stg_results` | Flattens grid, finish position, points, status, laps_completed. |
| `stg_driver_standings` | Cumulative points, wins, standings position per round. |
| `stg_laps` | **Jolpica format.** Parses "M:SS.mmm" → seconds. Flattens lap timing entries. |
| `stg_pit_stops` | **Jolpica format.** Parses duration string to seconds. |

**Removed (OpenF1-dependent):**
- ~~`stg_stints`~~ — No tyre compound data from Jolpica
- ~~`dim_sessions`~~ — Bridge table for OpenF1 session_key no longer needed

**Dimensions (tables → RAW_STAGING schema):**

| Model | Key Logic |
|-------|-----------|
| `dim_drivers` | Distinct driver_id, code, name from qualifying. |
| `dim_constructors` | Distinct constructor_id, name from qualifying. |
| `dim_dnf_status` | Seed CSV → maps 98 status strings to `mechanical` / `crash` / `finished` / `other`. |

**Marts (tables → RAW_ANALYTICS schema):**

| Model | Key Logic | Row count (24 rounds) |
|-------|-----------|----------------------|
| `mart_qualifying_h2h` | Self-join on constructor per round. Top-2 drivers by starts. Gap in ms. | 220 rows |
| `mart_race_h2h` | Teammate pairing. DNF category from `dim_dnf_status`, places gained. | 220 rows |
| `mart_points_trajectory` | Cumulative points per driver per round. | 519 rows |
| `mart_lap_pace` | Lap times by driver with constructor context. Filters safety car laps (>1.5× median). Replaces `mart_stint_pace`. | 26,122 rows |

### Phase 4 — Evidence.dev Dashboard ✅ (premium UI redesign)

| Item | Status |
|------|--------|
| `evidence/package.json` | Done — core-components + snowflake only |
| `npm install` | Done |
| `evidence.config.yaml` | Done — dark theme forced, F1 team color palette, basePath: `/f1-rivalry-dashboard` |
| `sources/snowflake/connection.yaml` | Done — uses `EVIDENCE_SOURCE__snowflake__*` env vars |
| Source SQL files | Done — 4 files (mart_qualifying_h2h, mart_race_h2h, mart_points_trajectory, mart_lap_pace) |
| `npm run sources` | ✅ Working — fetches all data from Snowflake |
| `npm run dev` | ✅ Working — dev server on localhost:3000 |
| `npm run build` | ✅ Working — static build succeeds |
| `pages/index.md` | ✅ Premium dark telemetry UI with card-based layout, HTML wrappers, accent colors |
| `pages/+layout.svelte` | ✅ Custom layout with Saira fonts, comprehensive CSS overrides, EvidenceDefaultLayout integration |

**UI Theme — Dark Motorsport Telemetry:**
- **Fonts:** Saira Condensed (headers, labels) + Saira (body) via Google Fonts — motorsport-inspired geometric sans
- **Colors:** F1 Red (#E10600) primary, Mercedes Teal (#00D2BE) accent, carbon-dark backgrounds (#0b0b12, #12121e)
- **Chart palette:** 10 F1 team-inspired colors (Ferrari red, Mercedes teal, Red Bull blue, McLaren papaya, etc.)
- **Layout features:**
  - Racing stripe gradient bar (red→teal) fixed at viewport top
  - Card-based sections with colored left accent bars (red, teal, blue, orange per section)
  - Stat cards with accent-colored values inside dark inset panels
  - Hero section with "FORMULA 1 ANALYTICS" badge and "TEAMMATE RIVALRY" title
  - Evidence header/sidebar/TOC/breadcrumbs hidden for clean dashboard feel
  - Staggered fade-in animation on section cards
  - DataTable with red header border, column group dividers, hover highlights
  - Dev-mode query viewers hidden via CSS (`.over-container { display: none }`)

**Dashboard sections:**
1. **Hero + Controls** — "TEAMMATE RIVALRY" hero with red accent, Season + Constructor dropdowns in dark controls bar
2. **Qualifying Battle** (red accent) — 3 stat cards (D1 Quali Wins, D2 Quali Wins, Avg Gap ms) + BarChart of qualifying gap per round
3. **Race Battle** (teal accent) — 4 stat cards (Race H2H Wins + Points per driver) + 3 new charts (Points Swing BarChart, Position Gap ScatterPlot, Cumulative H2H Wins LineChart) + compact scrollable DataTable for detail
4. **Points Trajectory** (blue accent) — LineChart of cumulative points for selected teammates only (filtered by constructor)
5. **Lap Pace Comparison** (orange accent) — Round dropdown + LineChart of teammate lap-by-lap times

**Key Evidence patterns used:**
- `defaultValue={2024}` (numeric via Svelte expression) on Dropdowns for prerender compatibility
- `${inputs.name.value}` in SQL queries for filtering (not JS `.filter()`)
- All SQL queries reference sources directly: `from snowflake.mart_qualifying_h2h` (not `from ${query_name}`)
- Numeric columns need unquoted `${inputs.*.value}`, string columns need quoted `'${inputs.*.value}'`
- BigValue `title` supports inline expressions: `title="{query[0].column} Label"`
- Cascading dropdowns: Season → Constructor → Round (each filters the next)
- Custom `+layout.svelte` must use `EvidenceDefaultLayout` component (handles splash screen removal)
- HTML `<div>` wrappers around Evidence components work in MDsveX for custom layout
- `hide_title: true` in frontmatter to suppress auto-generated h1

### Phase 5 — GitHub Actions CI/CD ✅ (scaffolded)

| Item | Path | Notes |
|------|------|-------|
| Workflow | `.github/workflows/deploy-evidence.yml` | Triggers on push to main + workflow_dispatch. Node 20. Snowflake creds from repo secrets. |
| GitHub PAT | `.env` | Token saved for Airflow → GitHub Actions trigger |

---

## Lessons Applied + New Lessons

| Lesson | Where Applied |
|--------|---------------|
| Use `ACCOUNTADMIN` (not SYSADMIN) | `snowflake_setup.sql`, `.env` |
| Single-line `airflow users create` | `docker-compose.yml` |
| No `PARSE_JSON(%s)` in executemany | All loaders use temp table → INSERT...SELECT |
| Only declare existing model paths | `dbt_project.yml` — staging, dimensions, marts only |
| `from __future__ import annotations` for Python 3.9 | Added to client modules |
| Snowflake connection needs `schema=RAW` for temp tables | `get_conn()` in `ingest_round.py` |
| dbt prepends default schema to custom schemas | Evidence connection points to `RAW_ANALYTICS` |
| Store Jolpica response as single VARIANT array row | Avoids UNIQUE constraint violations. Flatten in staging. |
| `PYTHONUNBUFFERED=1` for real-time output | Used in long-running ingestion scripts |
| Empty string Q times cause numeric errors | Fixed `stg_qualifying.sql` — added `!= ''` guards |
| Duplicate seed CSV rows cause unique test failure | Fixed `dnf_status_mapping.csv` |
| Evidence `{@const}` can only be inside `{#if}`, `{#each}` | Cannot use at top level in Evidence markdown |
| Evidence uses `EVIDENCE_SOURCE__<name>__<field>` env var pattern | Connection.yaml references these |
| OpenF1 API requires paid sponsorship + OAuth2 (since ~2025) | Replaced with Jolpica for laps + pit stops |
| Jolpica `/laps` endpoint paginates by timing entries, not laps | 100 entries/page ≈ 5 laps. Must paginate with offset. |
| Evidence Dropdown `defaultValue` must match column data type | Use `{2024}` for numeric columns, not `"2024"` |
| Evidence filtered SQL must reference sources directly | Use `from snowflake.mart_name`, not `from ${query_name}` |
| Evidence JS `.filter()` on data attributes causes Svelte store errors | Use SQL-based filtering with `${inputs.*.value}` instead |
| Numeric SQL filters must omit quotes | `where season = ${inputs.season.value}` not `= '${...}'` |
| **NEW:** Parallel API ingestion hits Jolpica 429 rate limits | Must run rounds sequentially with 2s delay between rounds |
| **NEW:** Evidence BigValue `title` supports inline expressions | `title="{query[0].column} Label"` for dynamic labels |
| **NEW:** F1 qualifying delta: show absolute gap with color for faster driver | Bigger bar = bigger margin. Don't use negative numbers (confusing). |
| **NEW:** Evidence `pages/+layout.svelte` REPLACES the default layout | Must import and use `EvidenceDefaultLayout` component, otherwise splash screen never removes and header/sidebar break |
| **NEW:** Evidence splash screen (`#__evidence_project_splash`) removed by `EvidenceDefaultLayout` onMount | Custom layouts without it leave the splash visible forever |
| **NEW:** Evidence SVG icons use `width="100%" height="100%"` HTML attrs | These expand to fill parent containers. Fix with `:global(svg[width="100%"]) { width: 1rem !important }` |
| **NEW:** Evidence DataTable does NOT use standard `<tbody>` wrapper | CSS targeting `tbody td` won't work. Must use `:global(td)` directly for cell styling |
| **NEW:** Evidence DataTable cell text defaults to `rgb(0,0,0)` (black) | On dark themes, must explicitly override with `:global(td) { color: #c8c8d4 !important }` |
| **NEW:** Evidence dev-mode query viewers have class `.over-container` | Hide with `:global(.over-container) { display: none !important }` to clean up dev view |
| **NEW:** Evidence theme colors configured in `evidence.config.yaml` under `theme.colors` | Set `appearance.default: dark` and `appearance.switcher: false` to force dark mode |
| **NEW:** Evidence assigns chart series colors by first-appearance order in data | To guarantee D1=red, D2=teal: add a `sort_priority` column and ORDER BY it so D1 rows always appear first |
| **NEW:** Evidence ScatterPlot `tooltipTitle` adds one extra column to tooltip | Use a formatted SQL string column (e.g. `'H2H Winner: ' || code || ' (P' || pos || ')'`) for rich tooltip headers |
| **NEW:** Evidence ScatterPlot tooltip shows redundant series line when `tooltipTitle` is set | Patch `Scatter.svelte` formatter to skip the `formatTitle(series)` block inside `if (tooltipTitle)` branch |
| **NEW:** Evidence auto-title-cases column aliases (`h2h_winner` → "H2h Winner") | Use quoted aliases (`"H2H Winner"`) to preserve exact casing in legends/tooltips |
| **NEW:** Evidence dark theme `--base-100` CSS var not applied to all content areas | Must add explicit `background: #0b0b12 !important` to `:global(html)`, `:global(body)`, `:global(main)`, `:global(article)` |
| **NEW:** Filtering out zero-value bars (`points_swing != 0`) removes invisible "Even" series | Prevents "Even" from consuming a color slot and shifting D1/D2 colors |

---

## Remaining Steps

### ~~Immediate (complete backfill)~~ ✅ DONE
- ~~All 24 rounds loaded for 2024, dbt run + test pass, Evidence sources refreshed, build succeeds~~
- ~~2025 season (24 rounds) ingested 2026-03-14 — batch script `scripts/ingest_season.py`~~

### Deploy to production
1. **Create GitHub repo**: `git remote add origin https://github.com/singhpriyanshu5/f1-rivalry-dashboard.git`
2. **Initial commit + push** to main
3. **Add repo secrets**: `EVIDENCE_SOURCE__snowflake__account`, `EVIDENCE_SOURCE__snowflake__username`, `EVIDENCE_SOURCE__snowflake__password`
4. **Enable GitHub Pages**: Settings → Pages → Source: GitHub Actions
5. **Verify deployment**: push triggers build → site live at `https://singhpriyanshu5.github.io/f1-rivalry-dashboard/`

### Polish
6. **Update Airflow DAG** — remove OpenF1 tasks, add Jolpica laps + pit stops
7. **Add `last_updated` footer** to dashboard
8. **Write README** with architecture diagram and setup instructions
9. **Clean up** deprecated OpenF1 raw tables and client code
10. **Optionally ingest 2023 season** for historical comparison

### ~~UI Redesign~~ ✅ DONE (2026-03-13)
- Dark telemetry theme with Saira fonts, F1 color palette
- Card-based layout with colored accent bars per section
- Custom `+layout.svelte` with `EvidenceDefaultLayout`, hidden header/sidebar
- Fixed: SVG icon sizing, DataTable black-on-black text, splash screen removal, query viewer hiding
- `npm run build` passes, all sections render correctly

### ~~Race Battle Visualization Upgrade~~ ✅ DONE (2026-03-14)
Replaced plain DataTable with 3 insight-rich charts in the Race Battle section:
- **Points Swing BarChart** — Signed bars (above zero = D1 scored more). Dynamic title with driver code. Series ordering fix ensures consistent red/teal colors across all constructors.
- **Position Gap ScatterPlot** — Dots above/below zero line showing finish position gap. `tooltipTitle` shows "H2H Winner: VER (P1)". Patched `Scatter.svelte` to remove redundant series line from tooltip when `tooltipTitle` is set.
- **Cumulative H2H Wins LineChart** — Running race win tally with `driver_order` column to ensure consistent color assignment (D1=red, D2=teal).
- **DataTable** kept as compact scrollable detail view (`rows=8`, `max-height: 320px`).
- **Points Trajectory** filtered to selected constructor's teammates only (was showing all 20 drivers).
- Stat card labels changed from "Race Wins" → "Race H2H Wins" for clarity.
- Hero section background fixed — forced `background: #0b0b12` on `html`, `body`, `main`, `article` to prevent washed-out light backgrounds.
- 3 new SQL queries added: `race_points_swing`, `race_position_gap`, `race_h2h_cumulative`.
