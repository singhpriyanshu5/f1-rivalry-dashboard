"""F1 Rivalry Dashboard — Master Pipeline DAG.

Flow: Jolpica API → Snowflake raw → dbt → trigger Evidence rebuild
Runs twice per race weekend:
  - Sunday  2am UTC (post-Saturday): qualifying data available
  - Monday  2am UTC (post-Sunday):  race results, standings, laps, pit stops available

Auto-detects the current season and most recent race round.
Skips non-race weekends gracefully (no data to ingest → short-circuits).

Manual trigger supports backfill via params:
  - mode: "latest" (default, auto-detect) or "backfill"
  - season: e.g. 2026
  - start_round / end_round: range of rounds to load
"""

from __future__ import annotations

import json
import os
import logging
import time
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from airflow.models.param import Param

import snowflake.connector
import requests as http_requests

from utils.jolpica_client import (
    fetch_qualifying, fetch_results, fetch_driver_standings,
    fetch_laps, fetch_pit_stops, fetch_schedule,
)

logger = logging.getLogger(__name__)

default_args = {
    "owner": "priyanshu",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def get_snowflake_conn():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ.get("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        database=os.environ.get("SNOWFLAKE_DATABASE", "F1_ANALYTICS"),
        schema="RAW",
    )


def _load_array_to_raw(records, table_name, season, round_num):
    """Store API response array as one VARIANT row per (season, round).

    DELETE+INSERT for idempotency. Uses temp table approach per lessons learned.
    """
    if not records:
        logger.info(f"No records for {table_name} — skipping")
        return

    conn = get_snowflake_conn()
    cur = conn.cursor()
    raw_table = f"RAW.RAW_{table_name.upper()}"
    source_label = f"jolpica/{season}/{round_num}/{table_name}"

    try:
        cur.execute(
            f"DELETE FROM {raw_table} WHERE season = %s AND round = %s",
            (season, round_num),
        )
        cur.execute("CREATE TEMPORARY TABLE _tmp_jolpica (json_str VARCHAR)")
        cur.execute(
            "INSERT INTO _tmp_jolpica (json_str) VALUES (%s)",
            (json.dumps(records, default=str),),
        )
        cur.execute(f"""
            INSERT INTO {raw_table} (raw_data, season, round, _ingested_at, _source_file)
            SELECT PARSE_JSON(json_str), {season}, {round_num},
                   CURRENT_TIMESTAMP(), '{source_label}'
            FROM _tmp_jolpica
        """)
        cur.execute("DROP TABLE _tmp_jolpica")
        logger.info(f"Loaded {len(records)} records (1 row) into {raw_table}")
    finally:
        cur.close()
        conn.close()


def _ingest_single_round(season, round_num):
    """Ingest all 6 data sources for a single round."""
    logger.info(f"Ingesting {season} R{round_num}...")

    data = fetch_qualifying(season, round_num)
    _load_array_to_raw(data, "qualifying", season, round_num)

    data = fetch_results(season, round_num)
    _load_array_to_raw(data, "results", season, round_num)

    data = fetch_driver_standings(season, round_num)
    _load_array_to_raw(data, "driver_standings", season, round_num)

    data = fetch_laps(season, round_num)
    _load_array_to_raw(data, "jolpica_laps", season, round_num)

    data = fetch_pit_stops(season, round_num)
    _load_array_to_raw(data, "jolpica_pit_stops", season, round_num)

    # Schedule: loaded once per season (round_num=0 key)
    races = fetch_schedule(season)
    _load_array_to_raw(races, "schedule", season, round_num=0)

    logger.info(f"Done — {season} R{round_num}")


# ─── Detect round or resolve backfill range ───────────────────────────────────

def detect_or_resolve_rounds(**context):
    """Determine which rounds to ingest.

    Scheduled runs: auto-detect latest round from the race calendar.
    Manual backfill: use params (season, start_round, end_round).

    Pushes a list of (season, round) tuples to XCom.
    Returns True if there's work to do (ShortCircuitOperator).
    """
    params = context.get("params", {})
    mode = params.get("mode", "latest")

    if mode == "backfill":
        season = int(params["season"])
        start_round = int(params["start_round"])
        end_round = int(params["end_round"])
        rounds = [(season, r) for r in range(start_round, end_round + 1)]
        logger.info(f"Backfill mode: {season} R{start_round}–R{end_round} ({len(rounds)} rounds)")
        context["ti"].xcom_push(key="rounds", value=rounds)
        return True

    # Auto-detect: find the latest round whose weekend has started
    today = datetime.utcnow().date()
    season = today.year

    races = fetch_schedule(season)
    if not races:
        logger.info(f"No races found for {season}")
        return False

    target_round = None
    for race in races:
        race_date = datetime.strptime(race["date"], "%Y-%m-%d").date()
        # Race weekend starts ~2 days before race day (Friday practice)
        weekend_start = race_date - timedelta(days=2)
        if weekend_start <= today:
            target_round = int(race["round"])

    if target_round is None:
        logger.info("No race weekend in progress — skipping")
        return False

    logger.info(f"Detected current round: {season} R{target_round}")
    context["ti"].xcom_push(key="rounds", value=[(season, target_round)])
    return True


# ─── Main ingestion task ──────────────────────────────────────────────────────

def ingest_rounds(**context):
    """Ingest all rounds from XCom (single round for scheduled, multiple for backfill).

    Runs sequentially with 2s delay between rounds to avoid Jolpica 429 rate limits.
    """
    rounds = context["ti"].xcom_pull(task_ids="detect_rounds", key="rounds")
    total = len(rounds)

    for i, (season, round_num) in enumerate(rounds, 1):
        logger.info(f"[{i}/{total}] Ingesting {season} R{round_num}")
        _ingest_single_round(season, round_num)

        if i < total:
            logger.info("Waiting 2s before next round (rate limit)...")
            time.sleep(2)

    logger.info(f"Ingestion complete — {total} round(s) loaded")


# ─── dbt run ─────────────────────────────────────────────────────────────────

def run_dbt(**context):
    """Run dbt deps + run + test from the mounted dbt/ directory."""
    import subprocess

    dbt_dir = "/opt/airflow/dbt"

    # Install dbt packages (e.g. dbt_utils) if not already present
    deps_result = subprocess.run(
        ["dbt", "deps", "--profiles-dir", dbt_dir, "--project-dir", dbt_dir],
        capture_output=True, text=True,
    )
    logger.info(deps_result.stdout)
    if deps_result.returncode != 0:
        logger.error(deps_result.stderr)
        raise RuntimeError(f"dbt deps failed: {deps_result.stderr}")

    # Run models
    run_result = subprocess.run(
        ["dbt", "run", "--profiles-dir", dbt_dir, "--project-dir", dbt_dir],
        capture_output=True, text=True,
    )
    logger.info(run_result.stdout)
    if run_result.returncode != 0:
        logger.error(run_result.stderr)
        raise RuntimeError(f"dbt run failed: {run_result.stderr}")

    # Run tests
    test_result = subprocess.run(
        ["dbt", "test", "--profiles-dir", dbt_dir, "--project-dir", dbt_dir],
        capture_output=True, text=True,
    )
    logger.info(test_result.stdout)
    if test_result.returncode != 0:
        logger.error(test_result.stderr)
        raise RuntimeError(f"dbt test failed: {test_result.stderr}")


# ─── Trigger Evidence rebuild ─────────────────────────────────────────────────

def trigger_evidence_build(**context):
    """Trigger GitHub Actions workflow to rebuild Evidence dashboard."""
    pat = os.environ.get("GITHUB_PAT")
    if not pat:
        logger.warning("GITHUB_PAT not set — skipping Evidence rebuild trigger")
        return

    resp = http_requests.post(
        "https://api.github.com/repos/singhpriyanshu5/f1-rivalry-dashboard/actions/workflows/deploy-evidence.yml/dispatches",
        json={"ref": "main"},
        headers={
            "Authorization": f"Bearer {pat}",
            "Accept": "application/vnd.github.v3+json",
        },
        timeout=15,
    )
    resp.raise_for_status()
    logger.info("Triggered Evidence rebuild via GitHub Actions")


# ─── DAG definition ──────────────────────────────────────────────────────────

with DAG(
    dag_id="f1_rivalry_pipeline",
    default_args=default_args,
    description="Jolpica API → Snowflake → dbt → Evidence (auto-detect or backfill)",
    schedule="0 2 * * 0,1",  # Sunday + Monday 2am UTC (post-Saturday, post-Sunday)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    params={
        "mode": Param(
            default="latest",
            type="string",
            enum=["latest", "backfill"],
            description="latest = auto-detect current round, backfill = load a range",
        ),
        "season": Param(default="2026", type="string", description="Season year (backfill mode)"),
        "start_round": Param(default="1", type="string", description="First round to load (backfill mode)"),
        "end_round": Param(default="2", type="string", description="Last round to load (backfill mode)"),
    },
    tags=["f1", "rivalry"],
) as dag:

    # Step 1: detect current round or resolve backfill range
    t_detect = ShortCircuitOperator(
        task_id="detect_rounds",
        python_callable=detect_or_resolve_rounds,
    )

    # Step 2: ingest all rounds (sequential with rate limiting)
    t_ingest = PythonOperator(
        task_id="ingest_rounds",
        python_callable=ingest_rounds,
    )

    # Step 3: dbt transformations
    t_dbt = PythonOperator(task_id="dbt_run", python_callable=run_dbt)

    # Step 4: trigger Evidence dashboard rebuild
    t_evidence = PythonOperator(task_id="trigger_evidence_build", python_callable=trigger_evidence_build)

    # Dependencies: linear pipeline
    t_detect >> t_ingest >> t_dbt >> t_evidence
