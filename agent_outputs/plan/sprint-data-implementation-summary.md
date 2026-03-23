# Sprint Data Implementation Summary

## Status: COMPLETE (All Steps Done)

**Branch:** `feature/sprint-data` (created from latest `main`)

---

## What Was Done

### Step 1: API Client — `airflow/dags/utils/jolpica_client.py`
- Added `fetch_sprint_results(season, round_num)` function
- URL: `{BASE_URL}/{season}/{round_num}/sprint.json`
- Parses `SprintResults` from response, returns `[]` for non-sprint rounds
- Verified: 2024 R5 (China) returns 20 drivers, 2024 R1 (non-sprint) returns `[]`

### Step 2: Snowflake DDL — `sql/snowflake_setup.sql`
- Added `RAW.RAW_SPRINT_RESULTS` table (same schema as `RAW_RESULTS`)
- Table created in Snowflake via direct DDL execution

### Step 3: Ingestion Scripts
- **`scripts/ingest_round.py`**: Added sprint fetch as step 3/7, updated all labels from X/6 to X/7
- **`airflow/dags/f1_pipeline_dag.py`**: Added `fetch_sprint_results` import, sprint fetch in `_ingest_single_round()`

### Step 4: dbt Staging
- **NEW** `dbt/models/staging/stg_sprint_results.sql` — mirrors `stg_results.sql`, reads from `raw_sprint_results`
- **Modified** `dbt/models/staging/stg_schedule.sql` — added `is_sprint_round` boolean column
- **Updated** `dbt/models/staging/schema.yml` — added `stg_sprint_results` with not_null tests
- **Updated** `dbt/models/sources.yml` — added `raw_sprint_results` source

### Step 5: dbt Marts
- **NEW** `dbt/models/marts/mart_sprint_h2h.sql` — mirrors `mart_race_h2h.sql` but reads from `stg_sprint_results`, uses `sprint_winner_code` column
- **Modified** `dbt/models/marts/mart_season_summary.sql`:
  - Added `sprint` CTE aggregating from `mart_sprint_h2h`
  - Added LEFT JOIN to sprint CTE
  - New columns: `d1_sprint_wins`, `d2_sprint_wins`, `d1_sprint_points`, `d2_sprint_points`, `sprint_rounds`, `sprint_verdict`
- **Updated** `dbt/models/marts/schema.yml` — added `mart_sprint_h2h` definition

### Step 6: Evidence Dashboard — `evidence/pages/index.md`
- Added 3 new SQL queries: `sprint_filtered`, `sprint_stats`, `sprint_points_by_round`
- Added Sprint nav pill (yellow accent, conditional on sprint data existing)
- Added Sprint verdict card in Season Verdict scorecard (conditional on `sprint_rounds > 0`)
- Added full Sprint Battle section between Race Battle and Points Trajectory:
  - BigValue cards: D1/D2 sprint wins, D1/D2 sprint points
  - BarChart: sprint points per round (grouped by driver)
  - DataTable: round-by-round sprint detail
- Added "Includes sprint race points" note under Points Trajectory
- Entire sprint section wrapped in `{#if sprint_filtered.length > 0}` conditional
- **`evidence/pages/+layout.svelte`**: Added yellow CSS for `.f1-section.yellow` and `.f1-nav-pill.yellow`

### Step 7: Narrative Generation — `airflow/dags/f1_pipeline_dag.py`
- Added sprint H2H query to `_query_mart_data()` (queries `MART_SPRINT_H2H`)
- Updated prompt template: added Sprint bullet item (with instruction to omit if no sprint data)

### Step 8a: Snowflake DDL Execution
- `RAW_SPRINT_RESULTS` table created successfully

### Step 8b: Data Backfill
- Re-ingested all 3 seasons:
  - **2024**: 24 rounds, 6 sprint rounds (R5, R6, R11, R19, R21, R23)
  - **2025**: 24 rounds, 6 sprint rounds (R2, R6, R13, R19, R21, R23)
  - **2026**: 2 rounds, 1 sprint round (R2)

### Step 8c: dbt Run + Test
- `dbt run`: 20/20 models passed (including new `stg_sprint_results`, `mart_sprint_h2h`, updated `mart_season_summary`)
- `dbt test`: 22/22 tests passed (including 3 new sprint tests)
- Verified data:
  - `mart_sprint_h2h`: 60 rows (2024), 60 rows (2025), 11 rows (2026)
  - `mart_season_summary`: Sprint columns populated correctly (e.g., VER 6-0 PER in 2024 sprints)

---

### Step 8d: Updated standalone `scripts/generate_narratives.py` with sprint data
- Added Sprint H2H query to `query_mart_data()` (mirrors DAG version)
- Added Sprint bullet to `build_prompt()` (with "omit if no sprint data" instruction)

### Step 8e: Regenerated narratives
- Ran `python scripts/generate_narratives.py` — all 39 pairings regenerated with sprint context
- Ran `dbt run --select mart_season_narrative` — refreshed narrative mart successfully

### Step 8f: Verified Evidence dashboard
- **Missing source fixed**: Created `evidence/sources/snowflake/mart_sprint_h2h.sql` (was missing, causing DuckDB catalog error)
- Sprint section renders correctly with BigValue cards, bar chart, and data table
- Sprint nav pill (yellow) visible in nav bar
- Sprint verdict card shows in Season Verdict scorecard
- Conditional `{#if sprint_filtered.length > 0}` works — section only appears when sprint data exists

---

## Files Modified/Created

| File | Action | Status |
|------|--------|--------|
| `airflow/dags/utils/jolpica_client.py` | Added `fetch_sprint_results()` | DONE |
| `sql/snowflake_setup.sql` | Added `RAW_SPRINT_RESULTS` DDL | DONE |
| `scripts/ingest_round.py` | Added sprint fetch step 3/7 | DONE |
| `airflow/dags/f1_pipeline_dag.py` | Sprint in ingestion + narrative query + prompt | DONE |
| `dbt/models/staging/stg_sprint_results.sql` | **NEW** — mirror of `stg_results.sql` | DONE |
| `dbt/models/staging/stg_schedule.sql` | Added `is_sprint_round` column | DONE |
| `dbt/models/staging/schema.yml` | Added `stg_sprint_results` | DONE |
| `dbt/models/sources.yml` | Added `raw_sprint_results` source | DONE |
| `dbt/models/marts/mart_sprint_h2h.sql` | **NEW** — mirror of `mart_race_h2h.sql` | DONE |
| `dbt/models/marts/mart_season_summary.sql` | Added sprint CTE + 6 new columns | DONE |
| `dbt/models/marts/schema.yml` | Added `mart_sprint_h2h` | DONE |
| `evidence/pages/index.md` | Sprint queries, verdict card, section, nav pill | DONE |
| `evidence/pages/+layout.svelte` | Yellow CSS for section + nav pill | DONE |
| `scripts/generate_narratives.py` | Added sprint query + prompt update | DONE |
| `evidence/sources/snowflake/mart_sprint_h2h.sql` | **NEW** — Evidence source query | DONE |

---

## Git Status
- Branch: `feature/sprint-data`
- No commits yet — all changes are unstaged
- Untracked new files: `stg_sprint_results.sql`, `mart_sprint_h2h.sql`, `mart_sprint_h2h.sql` (Evidence source), this summary
