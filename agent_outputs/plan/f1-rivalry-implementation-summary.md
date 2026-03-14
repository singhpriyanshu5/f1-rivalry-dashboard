# F1 Rivalry Dashboard — Implementation Summary

**Date:** 2026-03-14
**Status:** Full 2024 + 2025 seasons loaded (48 rounds) + 2026 R1-R2 via Airflow (50 rounds total). Dashboard fully working with premium dark telemetry UI, race battle visualization upgrade (3 insight charts), driver pairing selector for mid-season swaps, cascading dropdown fix, total race time gap chart, driver name legend, tooltip value-desc sorting, series color consistency via `seriesColors`, chart chronological ordering fix. dbt 14 models + 19 tests pass. Evidence build succeeds. `patch-package` preserves node_modules patches for deployment. **Deployed to GitHub Pages** at `https://singhpriyanshu5.github.io/f1-rivalry-dashboard/`.

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
- 2026 Rounds 1–2: **loaded** via Airflow DAG (R1 backfill + R2 scheduled run)
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
| `mart_qualifying_h2h` | Self-join on constructor per round. Pairs whoever actually qualified together (handles mid-season swaps). Gap in ms. | 478 rows |
| `mart_race_h2h` | Per-round teammate pairing (no season-wide top-2 filter). DNF category from `dim_dnf_status`, places gained. | 478 rows |
| `mart_points_trajectory` | Cumulative points per driver per round from standings. | 1,017 rows |
| `mart_lap_pace` | Lap times by driver with constructor context from `stg_results` (not qualifying). Filters safety car laps (>1.5× median). | 52,083 rows |

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
| **NEW:** Evidence `deployment.basePath` is the correct config key (not top-level `basePath`) | Without it, CSS/JS asset URLs miss the subpath prefix on GitHub Pages |
| **NEW:** Jolpica schedule API `/f1/{season}.json` returns race names + circuit locations | Use for `dim_races` dimension to add `round_label` to charts |
| **NEW:** String "R1", "R10" sort alphabetically wrong in dropdowns/charts | Zero-pad: `LPAD(round, 2, '0')` → "R01"..."R24". Alphabetical = chronological. |
| **NEW:** Top-2-by-starts pairing logic drops mid-season swap rounds | Remove `primary_drivers` filter; self-join per round pairs whoever actually raced together |
| **NEW:** `stg_qualifying` missing some drivers → `mart_lap_pace` drops their laps | Use `stg_results` for driver-constructor mapping (every starter has a result) |
| **NEW:** Standings API lists drivers under original constructor after mid-season swap | Filter Points Trajectory by driver codes from pairing, not by constructor_id |
| **NEW:** Evidence Dropdown `order` prop caused ghost pre-render entries to persist | Avoid `order` prop; make labels sort correctly by default (zero-padded numbers) |
| **NEW:** Evidence dropdowns render as `role="combobox"` buttons, not `<select>` | Playwright tests must click button by `aria-label`, then click option text in popover |
| **NEW:** Evidence Dropdown doesn't auto-reset selection when data changes | `dropdownOptionStore.removeOptions()` preserves selected stale options. Patch `Dropdown.svelte` with reactive block + `setTimeout(250ms)` to auto-select first option after batchUp completes |
| **NEW:** Evidence `batchUp` functions (addOptions, removeOptions, toggleSelected) have 100ms delay | In Svelte `{#each}`, new items create before old items destroy → addOptions fires before removeOptions. Can't rely on flags set in removeOptions to affect addOptions. Use setTimeout > 200ms instead |
| **NEW:** `{#key}` blocks don't reset Evidence dropdown selections | Evidence persists input values in `$inputs` store independent of component lifecycle. Destroying/recreating Dropdown doesn't clear the store entry |
| **NEW:** Blank lines inside Svelte component tags in MDsveX cause `</p>` parse errors | MDsveX interprets blank lines as paragraph breaks. Never put blank lines between component props and the closing `/>` or `>` |
| **NEW:** Evidence chart tooltip iterates `params` in reverse order | `_Chart.svelte` formatter uses `for (i = params.length-1; i >= 0; i--)`. Patch to sort by value descending for clearer readability |
| **NEW:** Evidence chart series colors assigned by first-appearance order in data | To control which driver gets red vs teal, ORDER BY with D1 first. Remove `sort=false` (safe with zero-padded round labels) so x-axis sorts independently |
| **NEW:** `patch-package` preserves node_modules patches across `npm install` | Add `"postinstall": "patch-package"` to package.json. Patch file at `patches/@evidence-dev+core-components+5.4.2.patch` must be committed to git |
| **NEW:** Vite caches pre-bundled node_modules deps in `node_modules/.vite` | Must delete `.vite` dir and restart dev server for node_modules patches to take effect |

---

## Remaining Steps

### ~~Immediate (complete backfill)~~ ✅ DONE
- ~~All 24 rounds loaded for 2024, dbt run + test pass, Evidence sources refreshed, build succeeds~~
- ~~2025 season (24 rounds) ingested 2026-03-14 — batch script `scripts/ingest_season.py`~~

### ~~Deploy to production~~ ✅ DONE
1. ~~**Create GitHub repo**: `git remote add origin https://github.com/singhpriyanshu5/f1-rivalry-dashboard.git`~~
2. ~~**Initial commit + push** to main~~
3. ~~**Add repo secrets**: `EVIDENCE_SOURCE__snowflake__account`, `EVIDENCE_SOURCE__snowflake__username`, `EVIDENCE_SOURCE__snowflake__password`~~
4. ~~**Enable GitHub Pages**: Settings → Pages → Source: GitHub Actions~~
5. ~~**Verify deployment**: push triggers build → site live at `https://singhpriyanshu5.github.io/f1-rivalry-dashboard/`~~
- GitHub Actions workflow at `.github/workflows/deploy-evidence.yml` auto-deploys on push to `main`
- `npm ci` triggers `postinstall` → `patch-package` applies node_modules patches automatically
- Subsequent deploys: just commit + push to `main`

### ~~Update Airflow DAG~~ ✅ DONE (2026-03-14)
- Removed OpenF1 entirely — all ingestion is Jolpica-only
- Schedule: `0 2 * * 0,1` (Sunday + Monday 2am UTC, post-Saturday + post-Sunday)
- Auto-detects current season + latest round via `ShortCircuitOperator` — no manual params for scheduled runs
- Short-circuits on non-race weekends (no wasted API calls)
- **Backfill mode**: manual trigger with `mode=backfill`, `season`, `start_round`, `end_round` params
- Rounds run sequentially with 2s delay (Jolpica 429 rate limit protection)
- Pipeline: detect_rounds → ingest_rounds → dbt_run → trigger_evidence_build
- `scripts/ingest_round.py` updated to include schedule ingestion (step 6/6)
- **F1 Airflow instance running** on `localhost:8081` (port 8081 webserver, 5433 Postgres) — separate from EV project
  - `COMPOSE_PROJECT_NAME=f1-airflow` isolates containers
  - `dbt-snowflake` installed in container, `../dbt` mounted at `/opt/airflow/dbt`
  - `dbt_run` task runs `dbt deps` → `dbt run` → `dbt test`
  - Credentials: admin/admin
- **2026 season loaded** via backfill (R1) + scheduled run (R2 qualifying). VER didn't qualify R1 — qualifying H2H only shows R2, race H2H shows both.
- **Jolpica client fix**: `fetch_laps` handles missing `position` field in timing entries (KeyError fix)
- **GITHUB_PAT** needs `Actions: Read and write` permission for workflow dispatch
- See: [`agent_outputs/plan/airflow-dag-scheduling.md`](./airflow-dag-scheduling.md) for full design notes

### Polish (remaining)
1. ~~**Update Airflow DAG** — remove OpenF1 tasks, add Jolpica laps + pit stops~~ ✅
2. ~~**Stand up F1 Airflow instance**~~ ✅ — running on port 8081
3. **Add `last_updated` footer** to dashboard
4. **Write README** with architecture diagram and setup instructions
5. **Clean up** deprecated OpenF1 raw tables and client code
6. **Optionally ingest 2023 season** for historical comparison

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

### ~~Race Location Labels~~ ✅ DONE (2026-03-14)
- Ingested race schedule for 2024 + 2025 into `RAW_SCHEDULE` table via Jolpica `/f1/{season}.json`
- New dbt models: `stg_schedule` (staging view), `dim_races` (dimension table with `round_label` = "R1 Sakhir")
- All 4 marts now join `dim_races` to include `round_label` and `locality`
- All chart x-axes use `round_label` instead of numeric round (e.g. "R1 Sakhir" instead of "1")
- Lap Pace round dropdown shows `round_label` as display label
- DataTable includes `locality` column for race location
- dbt: 14 models pass, 19 tests pass

### ~~Chart Ordering + Mid-Season Driver Swaps + Pairing Selector~~ ✅ DONE (2026-03-14)

**Chart ordering fix:**
- Zero-padded `round_label` in `dim_races`: `'R' || LPAD(round, 2, '0') || ' ' || locality` → "R01 Melbourne"
- Added `sort=false` to all 5 charts using `x=round_label` to preserve SQL ORDER BY
- Alphabetical order now equals chronological order — works in both charts and dropdowns

**Mid-season driver swap fix:**
- Removed `primary_drivers` CTE (top-2 by season starts) from `mart_qualifying_h2h` and `mart_race_h2h`
- Models now pair whoever actually raced/qualified together per round via self-join `driver_id < driver_id`
- Row counts increased from 449 → 478 (extra rounds from mid-season swaps now included)
- `mart_lap_pace` changed from `stg_qualifying` to `stg_results` for driver-constructor mapping (52,083 rows, up from 26,122)

**Driver Pairing selector:**
- New `pairings` SQL query: distinct `driver_1_code || '|' || driver_2_code` per season+constructor
- New "Driver Pairing" Dropdown in controls bar (Season → Constructor → Pairing cascade)
- All 11 filtered queries now include pairing filter: `driver_1_code || '|' || driver_2_code = '${inputs.pairing.value}'`
- Points Trajectory filters by `driver_code in (split_part(...))` instead of `constructor_id` (standings API lists drivers under original constructor)
- Example: 2025 Red Bull shows "LAW vs VER" (R01-R02) and "VER vs TSU" (R03-R24) as separate pairings

**Playwright validation tests:**
- `evidence/tests/validate-dashboard.spec.cjs` — 2 tests covering VER vs TSU and LAW vs VER scenarios
- Evidence uses `role="combobox"` buttons (not `<select>`), selected via `aria-label` + popover click
- Screenshots saved to `evidence/tests/screenshots/` for visual validation

### ~~Cascading Dropdown Fix~~ ✅ DONE (2026-03-14)
- **Problem:** Changing season/constructor kept stale pairing selection (e.g. VER|PER persisted when switching from 2024 to 2025)
- **Root cause:** Evidence's `dropdownOptionStore.removeOptions()` preserves selected options with `__removeOnDeselect = true` instead of removing them
- **Fix:** Patched `Dropdown.svelte` — reactive block detects when current selection no longer exists in query data, uses `setTimeout(250ms)` to auto-select first available option after `batchUp(100ms)` completes
- **Fix 2:** Patched `dropdownOptionStore.js` — `removeOptions()` now immediately removes stale selected options and sets `selectFirst = true`
- **`rounds_available` query** now also filters by pairing (was missing pairing filter)
- All patches preserved via `patch-package` → `patches/@evidence-dev+core-components+5.4.2.patch`
- `postinstall` script added to `package.json` to auto-apply patches after `npm install`

### ~~Total Race Time Gap Chart~~ ✅ DONE (2026-03-14)
- New `race_time_gap` SQL query: self-joins `mart_lap_pace` to sum lap times per driver per round, computes gap
- Signed BarChart in Lap Pace section — bars above/below zero show which driver's total race time was slower/faster
- Safety car laps already filtered (inherited from `mart_lap_pace`)
- Series colored by `faster_driver` with `sort_priority` column for D1-first ordering

### ~~UI Polish~~ ✅ DONE (2026-03-14)
- **Driver name legend:** New `f1-driver-legend` panel below controls showing full driver names (e.g. "DOO Jack Doohan vs GAS Pierre Gasly") with colored chips. Data from `race_filtered` query (`driver_1_name`, `driver_2_name` columns already in `mart_race_h2h`)
- **Stat card labels:** "Quali Wins" → "Quali Head-to-Head", "Race H2H Wins" → "Race Head-to-Head"
- **Chart titles:** All em-dashes (—) replaced with single dashes (-)
- **Tooltip sorting:** Patched `_Chart.svelte` tooltip formatter to sort entries by value descending (was reversed order). VER (16) now shows before TSU (1)
- **Series color consistency (partial):** All chart queries now order data so D1's code appears first (gets red). Removed `sort=false` from all charts (zero-padded round labels sort alphabetically = chronologically). Works for multi-round pairings but single-round edge cases (e.g. DOO vs GAS with 1 qualifying round) still show only one series color

### ~~Color Consistency Fix~~ ✅ DONE (2026-03-14)
- **Problem:** When only one driver appeared in a chart series, that driver got the first palette color (red) regardless of D1/D2 position
- **Fix:** Added `seriesColors` prop to all 7 charts — dynamically maps D1 code → `#E10600` (red) and D2 code → `#00D2BE` (teal) using Evidence's per-series color override: `seriesColors={{ [race_stats[0].d1_code]: '#E10600', [race_stats[0].d2_code]: '#00D2BE' }}`
- **Chart ordering fix:** `seriesColors` made the D1-first SQL `ORDER BY` unnecessary; changed all queries to `ORDER BY round` (chronological) and added `sort=false` to all charts to preserve SQL order
- **Race time gap title fix:** Corrected inverted label from "Positive = VER Slower" to "Positive = VER Faster"
- **DNF handling:** Race time gap chart compares only laps both drivers completed (via `lap_number` join). Added user-facing note: *"DNF rounds compare only laps both drivers completed. Safety car laps filtered."*
- **Round selector spacing:** Added `margin-top: 1.5rem` to `.f1-inline-control` for visual separation from chart above

### Lessons from this session

| Lesson | Detail |
|--------|--------|
| Evidence `seriesColors` prop maps series names to specific colors | `seriesColors={{ [dynamic_key]: '#hex' }}` overrides palette assignment. Defined in `applySeriesColors()` in `echarts.js`. |
| `seriesColors` removes need for D1-first data ordering | Color assignment is explicit, so SQL `ORDER BY` can be purely chronological |
| Must add `sort=false` when SQL ORDER BY matters | Evidence default sort overrides SQL order — sorts by value for BarChart, alphabetical for LineChart |
| Race time gap must handle DNFs fairly | Join on matching `lap_number` already compares only common laps; add explanatory note for users |
