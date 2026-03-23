# Plan: Add Sprint Race Data to F1 Rivalry Dashboard

## Context

The F1 rivalry dashboard currently has **zero sprint coverage**. Since 2021, F1 has sprint weekends (~6 per season) with Sprint Qualifying (Shootout) + Sprint Race in addition to regular Qualifying + Race. Sprint results affect championship standings and are a key rivalry dimension.

The Jolpica API provides sprint race results at `/f1/{season}/{round}/sprint.json` (same JSON structure as regular results). **Sprint qualifying is NOT available** via Jolpica — that endpoint doesn't exist. The schedule endpoint already includes `Sprint.date` fields that identify sprint weekends.

Points trajectory is already correct (standings API includes sprint points), but we can't see sprint-specific performance breakdowns.

---

## Implementation Plan

### Step 1: API Client — `airflow/dags/utils/jolpica_client.py`
Add `fetch_sprint_results(season, round_num)` following the exact `fetch_results()` pattern:
- URL: `{BASE_URL}/{season}/{round_num}/sprint.json`
- Parse: `races[0]["SprintResults"]`
- Returns `[]` for non-sprint rounds (API returns empty `Races: []`)

### Step 2: Snowflake DDL — `sql/snowflake_setup.sql`
Add `RAW.RAW_SPRINT_RESULTS` table (same schema as `RAW_RESULTS`):
```sql
CREATE TABLE IF NOT EXISTS RAW.RAW_SPRINT_RESULTS (
    raw_data VARIANT, season INTEGER, round INTEGER,
    _ingested_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file VARCHAR
);
```

### Step 3: Ingestion Scripts
**`scripts/ingest_round.py`** — Add step 7/7 for sprint results:
```python
print("7/7 Sprint results...")
data = fetch_sprint_results(season, round_num)
load_jolpica_array(data, "sprint_results", season, round_num)
```
Update all step labels from `X/6` to `X/7`.

**`airflow/dags/f1_pipeline_dag.py`** — Add sprint fetch to `_ingest_single_round()`, import `fetch_sprint_results`. Always attempt the fetch (API handles non-sprint rounds gracefully).

### Step 4: dbt Staging
**New: `dbt/models/staging/stg_sprint_results.sql`** — Mirrors `stg_results.sql` exactly, reads from `raw_sprint_results`. Same columns: `season, round, driver_id, driver_code, driver_name, constructor_id, constructor_name, grid_position, finish_position, points, status, laps_completed`.

**Modify: `dbt/models/staging/stg_schedule.sql`** — Add `is_sprint_round` boolean:
```sql
r.value:Sprint:date IS NOT NULL as is_sprint_round
```

**Update: `dbt/models/staging/schema.yml`** — Add `stg_sprint_results` model + tests.

### Step 5: dbt Marts
**New: `dbt/models/marts/mart_sprint_h2h.sql`** — Mirrors `mart_race_h2h.sql` exactly but reads from `stg_sprint_results`. Self-joins teammates, determines `sprint_winner_code`, includes DNF categories. Only produces rows for sprint rounds.

**Modify: `dbt/models/marts/mart_season_summary.sql`** — Add sprint CTE from `mart_sprint_h2h`:
- New columns: `d1_sprint_wins`, `d2_sprint_wins`, `sprint_verdict`, `d1_sprint_points`, `d2_sprint_points`, `sprint_rounds`
- LEFT JOIN (nullable for non-sprint seasons)

**Update: `dbt/models/marts/schema.yml`** — Add `mart_sprint_h2h` definition.

### Step 6: Evidence Dashboard — `evidence/pages/index.md`

**UX Approach: Dedicated Sprint section + Sprint verdict card**
- Sprint rounds are sparse (6/season) — a separate section avoids empty charts cluttering existing views
- Conditionally rendered: only shows when sprint data exists for the selected pairing
- Keeps the existing clean layout untouched

**Changes:**
1. Add Sprint verdict card to Season Verdict scorecard (conditional on `sprint_rounds > 0`)
2. Add "Sprint" pill to section nav bar (yellow accent color)
3. New Sprint section (positioned between Race Battle and Points Trajectory):
   - BigValue cards: D1/D2 sprint wins, D1/D2 sprint points
   - BarChart: sprint points per round (grouped by driver)
   - DataTable: round-by-round sprint detail (round, locality, grid, finish, points, winner)
4. Add note under Points Trajectory: "Includes sprint race points"
5. Wrap entire sprint section in `{#if sprint_filtered.length > 0}` conditional

**New SQL queries:**
- `sprint_filtered` — sprint H2H data filtered by season/constructor/pairing
- `sprint_stats` — aggregated sprint wins and points

### Step 7: Narrative Generation — `airflow/dags/f1_pipeline_dag.py`
- Add sprint H2H query to `_query_mart_data()`
- Include sprint context in narrative prompt template
- Claude will naturally weave sprint rivalry into the AI-generated narrative

### Step 8: Backfill
1. Run DDL to create `RAW_SPRINT_RESULTS` table
2. Re-ingest 2024 + 2025 seasons (updated script will fetch sprint data)
3. `dbt run` to materialize new models
4. Narratives will auto-regenerate (prompt hash changes)

---

## Files to Modify/Create

| File | Action |
|------|--------|
| `airflow/dags/utils/jolpica_client.py` | Add `fetch_sprint_results()` |
| `sql/snowflake_setup.sql` | Add `RAW_SPRINT_RESULTS` DDL |
| `scripts/ingest_round.py` | Add sprint fetch step 7/7 |
| `airflow/dags/f1_pipeline_dag.py` | Wire sprint into pipeline + narrative |
| `dbt/models/staging/stg_sprint_results.sql` | **New** — mirror of `stg_results.sql` |
| `dbt/models/staging/stg_schedule.sql` | Add `is_sprint_round` column |
| `dbt/models/staging/schema.yml` | Add `stg_sprint_results` |
| `dbt/models/sources.yml` | Add `raw_sprint_results` source |
| `dbt/models/marts/mart_sprint_h2h.sql` | **New** — mirror of `mart_race_h2h.sql` |
| `dbt/models/marts/mart_season_summary.sql` | Add sprint CTE + columns |
| `dbt/models/marts/schema.yml` | Add `mart_sprint_h2h` |
| `evidence/pages/index.md` | Add sprint section + verdict card |

## Verification
1. After API client change: test `fetch_sprint_results(2024, 5)` — 2024 R5 (China) was a sprint weekend, should return results
2. After ingestion: verify `RAW_SPRINT_RESULTS` has rows for sprint rounds only
3. After dbt: `dbt test` passes, `mart_sprint_h2h` has ~6 rows per season
4. After dashboard: Evidence build succeeds, sprint section shows for sprint-weekend pairings, hides for non-sprint pairings
5. End-to-end: select a 2024 pairing → sprint section visible with correct H2H data
