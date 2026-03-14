# F1 Teammate Rivalry Dashboard

An end-to-end data engineering project that visualizes Formula 1 teammate rivalries across qualifying, race results, points progression, and lap pace — built with a modern analytics stack.

**Live Dashboard:** [singhpriyanshu5.github.io/f1-rivalry-dashboard](https://singhpriyanshu5.github.io/f1-rivalry-dashboard/)

![System Architecture](agent_outputs/architecture/f1-system-architecture.png)

## Features

- **Qualifying Battle** — Head-to-head qualifying wins and average gap (ms) per round
- **Race Battle** — Points swing, position gap scatter, cumulative H2H wins, and detailed race results
- **Points Trajectory** — Season-long cumulative points for selected teammates
- **Lap Pace Comparison** — Lap-by-lap overlay and total race time gap per round
- **Mid-Season Driver Swaps** — Cascading dropdowns let you select specific driver pairings (e.g. 2025 Red Bull: LAW vs VER for R01-R02, VER vs TSU for R03-R24)
- **Dark Telemetry UI** — Motorsport-inspired theme with Saira fonts, F1 team colors, and card-based layout

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Data Source** | [Jolpica F1 API](https://github.com/jolpica/jolpica-f1) (qualifying, results, standings, laps, pit stops, schedule) |
| **Orchestration** | Apache Airflow (Dockerized, LocalExecutor) |
| **Warehouse** | Snowflake (3 schema layers: RAW → STAGING → ANALYTICS) |
| **Transformation** | dbt Core (14 models, 19 tests) |
| **Dashboard** | [Evidence.dev](https://evidence.dev) (static site, Markdown + SQL) |
| **CI/CD** | GitHub Actions → GitHub Pages |

## Architecture

```
Jolpica API → Python Ingestion → Snowflake RAW (VARIANT)
                                      ↓
                                 dbt Staging (flatten + parse)
                                      ↓
                                 dbt Marts (H2H, trajectory, pace)
                                      ↓
                                 Evidence.dev → GitHub Pages
```

**Key decisions:**
- S3 layer skipped — data flows API → Snowflake directly
- OpenF1 replaced with Jolpica (OpenF1 requires paid sponsorship since ~2025)
- API responses stored as single VARIANT array row per (season, round) for idempotent DELETE+INSERT

## Project Structure

```
f1-rivalry-dashboard/
├── airflow/                  # Airflow Docker setup + DAGs
│   ├── dags/
│   │   ├── f1_pipeline_dag.py
│   │   └── utils/            # Jolpica API client
│   ├── docker-compose.yml
│   └── Dockerfile
├── dbt/                      # dbt transformations
│   ├── models/
│   │   ├── staging/          # stg_qualifying, stg_results, stg_laps, etc.
│   │   ├── dimensions/       # dim_drivers, dim_constructors, dim_races, dim_dnf_status
│   │   └── marts/            # mart_qualifying_h2h, mart_race_h2h, mart_points_trajectory, mart_lap_pace
│   ├── seeds/                # dnf_status_mapping.csv
│   └── dbt_project.yml
├── evidence/                 # Evidence.dev dashboard
│   ├── pages/
│   │   ├── index.md          # Dashboard page (SQL + Svelte components)
│   │   └── +layout.svelte    # Custom dark theme layout
│   ├── sources/snowflake/    # Source SQL queries
│   ├── patches/              # patch-package fixes for Evidence components
│   └── evidence.config.yaml
├── scripts/                  # Standalone ingestion scripts
│   ├── ingest_round.py       # Ingest single round: python ingest_round.py 2024 1
│   ├── ingest_season.py      # Ingest full season with rate limiting
│   └── test_apis.py          # API connectivity test
├── sql/
│   └── snowflake_setup.sql   # DDL for raw tables
└── .github/workflows/
    └── deploy-evidence.yml   # CI/CD: build Evidence → deploy to GitHub Pages
```

## Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose (for Airflow)
- Snowflake account
- dbt Core (`pip install dbt-snowflake`)

### 1. Clone & Configure

```bash
git clone https://github.com/singhpriyanshu5/f1-rivalry-dashboard.git
cd f1-rivalry-dashboard
cp .env.example .env
# Fill in Snowflake credentials in .env
```

### 2. Snowflake Setup

```bash
# Run the DDL to create database, schemas, and raw tables
# Execute sql/snowflake_setup.sql in your Snowflake worksheet
```

### 3. Ingest Data

```bash
pip install snowflake-connector-python requests pandas python-dotenv

# Single round
python scripts/ingest_round.py 2024 1

# Full season (sequential with rate limiting)
python scripts/ingest_season.py 2024
```

> **Note:** Jolpica rate-limits at ~30 req/min. The season script handles this with 2s delays between rounds.

### 4. Run dbt

```bash
cd dbt
dbt deps
dbt seed        # Load dnf_status_mapping.csv
dbt run         # Build 14 models
dbt test        # Run 19 tests
```

### 5. Run Evidence Dashboard (local)

```bash
cd evidence
npm install          # postinstall runs patch-package automatically
npm run sources      # Fetch data from Snowflake
npm run dev          # Dev server at localhost:3000
```

### 6. Build & Deploy

Pushing to `main` triggers the GitHub Actions workflow which builds Evidence and deploys to GitHub Pages.

```bash
# Or build locally
cd evidence
npm run build        # Static output in evidence/build/
```

**Required GitHub repo secrets for CI/CD:**
- `EVIDENCE_SOURCE__snowflake__account`
- `EVIDENCE_SOURCE__snowflake__username`
- `EVIDENCE_SOURCE__snowflake__password`

## Data Coverage

| Season | Rounds | Status |
|--------|--------|--------|
| 2024 | 1–24 | Fully loaded |
| 2025 | 1–24 | Fully loaded |

## dbt Model Lineage

```
RAW_QUALIFYING ──→ stg_qualifying ──→ mart_qualifying_h2h
RAW_RESULTS ────→ stg_results ─────→ mart_race_h2h
RAW_DRIVER_STANDINGS → stg_driver_standings → mart_points_trajectory
RAW_JOLPICA_LAPS ──→ stg_laps ────→ mart_lap_pace
RAW_JOLPICA_PIT_STOPS → stg_pit_stops
RAW_SCHEDULE ───→ stg_schedule ──→ dim_races ──→ (all marts)
                                    dim_drivers
                                    dim_constructors
seeds/dnf_status_mapping.csv ─────→ dim_dnf_status ──→ mart_race_h2h
```

## License

MIT
