# F1 Teammate Rivalry Dashboard — Implementation Plan

## Context

**Problem:** In F1, the only fair driver comparison is between teammates (same car), but most analysis stops at championship standings. This project builds a fully automated data pipeline and static dashboard that surfaces the full teammate rivalry story — qualifying pace gaps, race execution, DNF cost, tire management — for any constructor across a selected season.

**Outcome:** A public, no-login-required dashboard at `https://singhpriyanshu5.github.io/f1-rivalry-dashboard/` powered by Evidence.dev on GitHub Pages. Data flows from F1 APIs → S3 → Snowflake → dbt → Evidence build → GitHub Pages.

**Hosting decision:** GitHub Pages is ideal. Evidence.dev compiles to a fully static site — all Snowflake data is fetched at build time and baked into HTML/JS. No server needed.

---

## Directory Structure

Create at `/Users/priyanshusingh/Documents/ai_coding_projects/f1-rivalry-dashboard/`:

```
f1-rivalry-dashboard/
├── .env                          # Secrets (never committed)
├── .env.example                  # Template with required var names
├── .gitignore
├── README.md
├── agent_outputs/                # Claude planning/analysis docs
│
├── airflow/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt          # snowflake-connector-python, requests, boto3, pandas
│   └── dags/
│       ├── f1_pipeline_dag.py    # Master DAG orchestrating all steps
│       ├── utils/
│       │   ├── jolpica_client.py # API fetch + rate limiting for Jolpica
│       │   ├── openf1_client.py  # API fetch + throttling for OpenF1
│       │   └── s3_helpers.py     # S3 upload with partitioning
│
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml              # All creds via env_var()
│   ├── packages.yml              # dbt_utils
│   ├── models/
│   │   ├── sources.yml
│   │   ├── staging/
│   │   │   ├── stg_qualifying.sql
│   │   │   ├── stg_results.sql
│   │   │   ├── stg_driver_standings.sql
│   │   │   ├── stg_laps.sql
│   │   │   ├── stg_stints.sql
│   │   │   ├── stg_pit_stops.sql
│   │   │   └── schema.yml
│   │   ├── dimensions/
│   │   │   ├── dim_drivers.sql
│   │   │   ├── dim_constructors.sql
│   │   │   ├── dim_sessions.sql      # Bridges Jolpica round ↔ OpenF1 session_key
│   │   │   ├── dim_dnf_status.sql    # From seed
│   │   │   └── schema.yml
│   │   └── marts/
│   │       ├── mart_qualifying_h2h.sql
│   │       ├── mart_race_h2h.sql
│   │       ├── mart_points_trajectory.sql
│   │       ├── mart_stint_pace.sql
│   │       └── schema.yml
│   ├── seeds/
│   │   └── dnf_status_mapping.csv    # Maps ~120 Jolpica status strings → category
│   └── tests/
│
├── evidence/                         # Evidence.dev project (npx degit evidence-dev/template)
│   ├── evidence.config.yaml          # basePath: /f1-rivalry-dashboard
│   ├── package.json
│   ├── sources/
│   │   └── snowflake/
│   │       └── connection.yaml
│   └── src/
│       └── pages/
│           ├── index.md              # Season + constructor selector
│           └── rivalry.md            # Main dashboard with all 6 widgets
│
├── .github/
│   └── workflows/
│       └── deploy-evidence.yml       # Build Evidence → deploy to GitHub Pages
│
├── sql/
│   └── snowflake_setup.sql           # CREATE DATABASE, schemas, raw tables, stage
│
└── scripts/
    └── test_apis.py                  # Quick API connectivity check
```

---

## Phase 0 — Project Scaffold & Infrastructure

**Goal:** Repo exists, Snowflake ready, APIs reachable, Airflow boots locally.

**Steps:**
1. Create `f1-rivalry-dashboard/` with the directory tree above
2. `git init` → connect remote to `https://github.com/singhpriyanshu5/f1-rivalry-dashboard`
3. Create `.env` with Snowflake, AWS, and Airflow vars
   - **Lesson learned:** Use `SNOWFLAKE_ROLE=ACCOUNTADMIN` (not SYSADMIN)
4. Create `.env.example` (same keys, no values)
5. Create `.gitignore` (include `evidence/.evidence/`, `evidence/build/`, `evidence/node_modules/`, `.env`, `*.parquet`, `__pycache__/`)
6. Write `sql/snowflake_setup.sql`:
   - `CREATE DATABASE IF NOT EXISTS F1_ANALYTICS`
   - Schemas: `RAW`, `STAGING`, `ANALYTICS`
   - 6 raw tables with `VARIANT` column + `_ingested_at` + `_source_file`
   - External stage pointing to S3 bucket with JSON file format
7. Write `scripts/test_apis.py` — hit one endpoint each from Jolpica and OpenF1
8. Create `airflow/Dockerfile` + `docker-compose.yml` (LocalExecutor, Postgres backend)
   - **Lesson learned:** Put `airflow users create` on a single line in docker-compose.yml
9. `airflow/requirements.txt`: snowflake-connector-python, requests, boto3, pandas

**Verification:**
- `docker compose up` → Airflow webserver at `localhost:8080`
- `python scripts/test_apis.py` → both APIs return 200
- Run `snowflake_setup.sql` → all objects created

---

## Phase 1 — Ingestion DAGs (API → S3 Bronze)

**Goal:** Airflow fetches F1 data and writes partitioned JSON to S3.

**S3 partition scheme:** `s3://{bucket}/{table_name}/season={YYYY}/round={RR}/{table_name}.json`

**Jolpica ingestion** (3 parallel tasks):
- `fetch_qualifying(season, round)` → `GET /{season}/{round}/qualifying.json`
- `fetch_results(season, round)` → `GET /{season}/{round}/results.json`
- `fetch_standings(season, round)` → `GET /{season}/driverStandings/{round}.json`
- Rate limit: `time.sleep(0.5)` between requests, retry on 429

**OpenF1 ingestion** (sequential: sessions first, then laps/stints/pits):
- `fetch_sessions(season)` → `GET /sessions?year={season}&session_name=Race`
- For each session_key: fetch laps, stints, pit stops
- Derive round number by sorting sessions by date (bridge to Jolpica)
- Throttle: 0.3s between requests

**Master DAG** (`f1_pipeline_dag.py`):
- `[jolpica_tasks, openf1_tasks] >> s3_to_snowflake >> dbt_run >> trigger_evidence_build`
- Scheduled weekly during F1 season, `catchup=False`

**Verification:**
- Trigger with `{"season": "2024", "round": "1"}` → check S3 for files
- Spot-check JSON structure

---

## Phase 2 — S3 → Snowflake Raw Load

**Goal:** JSON from S3 lands in Snowflake raw tables.

**Approach:** `COPY INTO` via Snowflake connector in Airflow tasks (explicit, debuggable).

- 6 parallel tasks, one per raw table
- Use `MERGE` for idempotency (keyed on season+round+driver_id for round-level, session_key+driver_number+lap_number for lap-level)
- **Lesson learned:** Don't use `PARSE_JSON(%s)` in `executemany` VALUES — use temp table approach (insert as VARCHAR, then INSERT...SELECT with PARSE_JSON)

**Verification:**
- `SELECT COUNT(*) FROM raw.raw_qualifying WHERE season = 2024` → ~20 rows/round
- `SELECT * FROM raw.raw_laps LIMIT 10` → VARIANT column has expected fields

---

## Phase 3 — dbt Transformations

**Goal:** Bronze → Silver → Gold. All tests pass.

### Staging (views in STAGING schema)
Each model flattens VARIANT JSON with type casting:
- `stg_qualifying` — parse time strings ("1:23.456") into milliseconds, handle NULLs for Q2/Q3 no-times
- `stg_results` — grid, position, points, status, laps_completed
- `stg_driver_standings` — cumulative points per round
- `stg_laps` — lap_duration_s, sector times, pit out lap flag
- `stg_stints` — compound, stint start/end laps, tyre age
- `stg_pit_stops` — pit duration

### Dimensions (tables in STAGING schema)
- `dim_drivers` — driver_id, name, code, nationality
- `dim_constructors` — constructor_id, name, nationality
- **`dim_sessions`** — Critical bridge table mapping `(season, round)` ↔ `openf1_session_key` by joining on date + circuit
- `dim_dnf_status` — from seed CSV, maps ~120 status strings → `mechanical` / `crash` / `finished` / `other`

### Marts (tables in ANALYTICS schema)
- **`mart_qualifying_h2h`** — self-join stg_qualifying on (season, round, constructor_id) for teammate pairs. Columns: gap_ms, who was ahead. Season-level aggregation for H2H record.
- **`mart_race_h2h`** — same pattern on stg_results. Includes grid/finish positions, DNF category from dim_dnf_status, projected points lost on DNF.
- **`mart_points_trajectory`** — cumulative points per driver per round from stg_driver_standings.
- **`mart_stint_pace`** — join stg_laps ↔ stg_stints via dim_sessions. Filter safety car laps (>1.5x median duration). Output: lap_in_stint, lap_duration_s, compound, driver.

### Key modeling decisions
- Teammate pairing: self-join on constructor_id per round. Handle mid-season driver swaps by filtering to the 2 drivers with most starts per season.
- Best qualifying time: `COALESCE(q3_time_ms, q2_time_ms, q1_time_ms)`
- **Lesson learned:** Only declare model paths in dbt_project.yml that actually exist as directories

**Verification:**
- `dbt debug` → connection OK
- `dbt seed` → dnf_status_mapping loads
- `dbt run` → all models succeed
- `dbt test` → all pass
- Spot-check: query mart_qualifying_h2h for 2024 Red Bull

---

## Phase 4 — Evidence.dev Dashboard

**Goal:** Static dashboard with all 6 widgets, buildable locally.

**Setup:**
```bash
cd f1-rivalry-dashboard/
npx degit evidence-dev/template evidence
cd evidence && npm install
```

**Config:**
- `evidence.config.yaml`: `basePath: /f1-rivalry-dashboard`
- `sources/snowflake/connection.yaml`: account, username, password, database=F1_ANALYTICS, schema=ANALYTICS

**Pages:**

`index.md` — Landing page with:
- `<Dropdown>` for season selection (2022-2025)
- `<Dropdown>` for constructor (populated based on season)

`rivalry.md` — Main dashboard receiving season + constructor params:

| Widget | Component | Source Mart |
|--------|-----------|-------------|
| 1. H2H Scorecard | 4x `<BigValue>` tiles | mart_qualifying_h2h, mart_race_h2h (aggregated) |
| 2. Qualifying Delta Arc | `<LineChart>` with referenceLine at 0 | mart_qualifying_h2h |
| 3. Grid vs Finish Scatter | `<ScatterPlot>` with diagonal referenceLine | mart_race_h2h |
| 4. DNF Cost Stacked Bar | `<BarChart type="stacked">` | mart_race_h2h (DNF rows) |
| 5. Stint Pace Degradation | `<Dropdown>` + `<LineChart>` | mart_stint_pace |
| 6. Points Trajectory | `<AreaChart>` with 2 series | mart_points_trajectory |

**Verification:**
- `npm run dev` → local server at `localhost:3000`
- All 6 widgets render for 2024 Red Bull
- `npm run build` → output in `build/`

---

## Phase 5 — GitHub Actions CI/CD

**Goal:** Push to main → Evidence builds → GitHub Pages deploys.

**`.github/workflows/deploy-evidence.yml`:**
- Trigger: push to main + workflow_dispatch (for Airflow to trigger)
- Steps: checkout → setup Node 20 → npm ci → npm run sources → npm run build → upload-pages-artifact → deploy-pages
- Snowflake creds via repository secrets: `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`

**GitHub repo setup:**
- Settings → Pages → Source: GitHub Actions
- Add repository secrets for Snowflake connection

**Airflow trigger:** Last DAG task hits GitHub Actions API `POST /repos/.../dispatches` with a `GITHUB_PAT` to kick off rebuilds after dbt completes.

**Verification:**
- Push to main → Actions tab shows green run
- `https://singhpriyanshu5.github.io/f1-rivalry-dashboard/` loads the dashboard
- Manual workflow_dispatch → site rebuilds

---

## Phase 6 — Integration Test & Polish

**Goal:** Full pipeline runs end-to-end unattended.

1. Run full pipeline for 2024 season (all rounds)
2. Verify all widgets for multiple constructor pairings (Red Bull, Ferrari, McLaren, Mercedes)
3. Add `last_updated` timestamp in dashboard footer (`MAX(_ingested_at)` from raw)
4. Add error handling in DAGs (alert on failure)
5. Write README with architecture diagram and setup instructions
6. Test on mobile — should load in <3 seconds

**Final verification:**
- API → S3 → Snowflake → dbt → Evidence → GitHub Pages — all green
- Share URL with someone — works with no login
- Switch between 3+ constructors — all render correctly

---

## Key Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| OpenF1 session_key ↔ Jolpica round mapping | Sort sessions by date, cross-reference with Jolpica schedule. Test with 2024 first. |
| Jolpica 200 req/hr rate limit during backfill | 0.5s sleep = 120 req/hr. 24 rounds × 3 endpoints = 72 requests — well within limit. |
| Qualifying time parsing edge cases (no Q2/Q3 time) | Handle NULLs in stg_qualifying. Use COALESCE(q3, q2, q1). |
| Constructor with 3+ drivers (mid-season swap) | Filter to 2 drivers with most starts per constructor/season. |
| Evidence build fails in CI | Test `npm run sources` + `npm run build` locally before pushing. Pin Evidence version. |

---

## Critical Files (ordered by implementation priority)

1. `sql/snowflake_setup.sql` — Foundation: database, schemas, raw tables
2. `airflow/dags/utils/jolpica_client.py` — Core API interaction with rate limiting
3. `airflow/dags/utils/openf1_client.py` — Session key resolution + lap data fetch
4. `airflow/dags/f1_pipeline_dag.py` — Master DAG wiring everything together
5. `dbt/models/dimensions/dim_sessions.sql` — Critical bridge between data sources
6. `dbt/models/marts/mart_qualifying_h2h.sql` — Teammate self-join pattern (template for other marts)
7. `dbt/seeds/dnf_status_mapping.csv` — Manual curation of ~120 status codes
8. `evidence/src/pages/rivalry.md` — Main dashboard with all 6 widgets
9. `.github/workflows/deploy-evidence.yml` — CI/CD connecting pipeline to public site
