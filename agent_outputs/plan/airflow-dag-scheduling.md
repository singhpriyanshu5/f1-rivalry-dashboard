# Airflow DAG Scheduling - Design Notes

**Date:** 2026-03-14

## Schedule

Cron: `0 2 * * 0,1` — Sunday + Monday 2am UTC

| Run | Timing | What's available on Jolpica |
|-----|--------|----------------------------|
| Sunday 2am UTC | Post-Saturday | Qualifying results |
| Monday 2am UTC | Post-Sunday | Race results, standings, laps, pit stops |

Non-race weekends: `detect_rounds` short-circuits — no API calls, no dbt, no deploy.

## Two Modes

### 1. Scheduled (mode=latest)
- Auto-detects current season (`utcnow().year`) and latest round where `race_date - 2 days <= today`
- Loads single round, runs dbt, triggers Evidence rebuild
- Saturday's qualifying-only load gets re-upserted on Sunday (idempotent DELETE+INSERT)

### 2. Manual Backfill (mode=backfill)
- Trigger via Airflow UI or CLI with params: `mode=backfill`, `season=2026`, `start_round=1`, `end_round=2`
- Runs rounds sequentially with 2s delay between rounds (Jolpica 429 rate limit protection)
- Same pipeline: ingest → dbt → Evidence rebuild

## Infra Note

The running Airflow instance (`docker compose` on port 8080) is from `ev-charging-stations-dashboard`, not f1-rivalry-dashboard. Options:
1. Start F1 Airflow on a different port (e.g. 8081)
2. Share one Airflow across projects (copy DAGs + utils into shared dags dir)
3. Use standalone scripts (`scripts/ingest_season.py`) for now, bring up F1 Airflow later

## How to Run Backfill Right Now (no Airflow needed)

```bash
cd f1-rivalry-dashboard
source .env  # or export SNOWFLAKE_* vars
python scripts/ingest_season.py 2026 1 2
```

This loads 2026 rounds 1-2 into Snowflake, then run dbt + Evidence rebuild manually.

## Files Changed

- `airflow/dags/f1_pipeline_dag.py` — rewritten: removed OpenF1, added auto-detect + backfill mode
- `scripts/ingest_round.py` — added schedule ingestion (step 6/6)
