"""F1 Rivalry Dashboard — Master Pipeline DAG.

Flow: API fetch → Snowflake raw → dbt → trigger Evidence rebuild
Scheduled weekly during F1 season, catchup=False.
"""

import json
import os
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models.param import Param

import snowflake.connector
import requests as http_requests

from utils.jolpica_client import fetch_qualifying, fetch_results, fetch_driver_standings, fetch_schedule
from utils.openf1_client import fetch_race_sessions, fetch_laps, fetch_stints, fetch_pit_stops

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
    )


def _load_records_to_raw(
    records: list[dict],
    table_name: str,
    season: int,
    round_num: int,
    unique_keys: list[str],
    extra_cols: str,
    extra_vals: str,
    source_label: str,
):
    """Load JSON records directly into Snowflake raw table.

    Uses temp table approach: insert as VARCHAR, then INSERT...SELECT with PARSE_JSON.
    MERGE for idempotency.
    """
    if not records:
        logger.info(f"No records for {table_name} season={season} round={round_num}")
        return

    conn = get_snowflake_conn()
    cur = conn.cursor()
    raw_table = f"RAW.RAW_{table_name.upper()}"

    try:
        cur.execute(f"CREATE TEMPORARY TABLE _tmp_{table_name} (json_str VARCHAR)")

        for record in records:
            cur.execute(
                f"INSERT INTO _tmp_{table_name} (json_str) VALUES (%s)",
                (json.dumps(record, default=str),)
            )

        merge_key_conditions = " AND ".join(
            f"target.{k} = source.{k}" for k in unique_keys
        )

        cur.execute(f"""
            MERGE INTO {raw_table} AS target
            USING (
                SELECT
                    PARSE_JSON(json_str) AS raw_data,
                    {extra_vals},
                    CURRENT_TIMESTAMP() AS _ingested_at,
                    '{source_label}' AS _source_file
                FROM _tmp_{table_name}
            ) AS source ({', '.join(['raw_data', *unique_keys, '_ingested_at', '_source_file'])})
            ON {merge_key_conditions}
            WHEN MATCHED THEN UPDATE SET
                raw_data = source.raw_data,
                _ingested_at = source._ingested_at,
                _source_file = source._source_file
            WHEN NOT MATCHED THEN INSERT
                (raw_data, {extra_cols}, _ingested_at, _source_file)
                VALUES (source.raw_data, {', '.join(f'source.{k}' for k in unique_keys)}, source._ingested_at, source._source_file)
        """)

        logger.info(f"Loaded {len(records)} records into {raw_table}")
    finally:
        cur.close()
        conn.close()


# ─── Jolpica: fetch + load in one step ───────────────────────────────────────

def ingest_qualifying(**context):
    season = int(context["params"]["season"])
    round_num = int(context["params"]["round"])
    data = fetch_qualifying(season, round_num)
    _load_records_to_raw(
        records=data,
        table_name="qualifying",
        season=season,
        round_num=round_num,
        unique_keys=["season", "round"],
        extra_cols="season, round",
        extra_vals=f"{season}, {round_num}",
        source_label=f"jolpica/{season}/{round_num}/qualifying",
    )


def ingest_results(**context):
    season = int(context["params"]["season"])
    round_num = int(context["params"]["round"])
    data = fetch_results(season, round_num)
    _load_records_to_raw(
        records=data,
        table_name="results",
        season=season,
        round_num=round_num,
        unique_keys=["season", "round"],
        extra_cols="season, round",
        extra_vals=f"{season}, {round_num}",
        source_label=f"jolpica/{season}/{round_num}/results",
    )


def ingest_standings(**context):
    season = int(context["params"]["season"])
    round_num = int(context["params"]["round"])
    data = fetch_driver_standings(season, round_num)
    _load_records_to_raw(
        records=data,
        table_name="driver_standings",
        season=season,
        round_num=round_num,
        unique_keys=["season", "round"],
        extra_cols="season, round",
        extra_vals=f"{season}, {round_num}",
        source_label=f"jolpica/{season}/{round_num}/standings",
    )


# ─── OpenF1: fetch sessions, then laps/stints/pits ───────────────────────────

def ingest_openf1_data(**context):
    """Fetch sessions + laps + stints + pits for the target round, load directly to Snowflake."""
    season = int(context["params"]["season"])
    round_num = int(context["params"]["round"])

    sessions = fetch_race_sessions(season)
    if round_num > len(sessions):
        logger.warning(f"Round {round_num} not found in OpenF1 sessions for {season}")
        return

    session = sessions[round_num - 1]
    session_key = session["session_key"]
    logger.info(f"OpenF1 session_key={session_key} for {season} round {round_num}")

    # Load session metadata
    _load_records_to_raw(
        records=[session],
        table_name="sessions",
        season=season,
        round_num=round_num,
        unique_keys=["session_key"],
        extra_cols="session_key, season, round",
        extra_vals=f"PARSE_JSON(json_str):session_key::INTEGER, {season}, {round_num}",
        source_label=f"openf1/{season}/{round_num}/sessions",
    )

    # Fetch and load laps
    laps = fetch_laps(session_key)
    _load_records_to_raw(
        records=laps,
        table_name="laps",
        season=season,
        round_num=round_num,
        unique_keys=["session_key", "driver_number", "lap_number"],
        extra_cols="session_key, driver_number, lap_number",
        extra_vals=(
            "PARSE_JSON(json_str):session_key::INTEGER, "
            "PARSE_JSON(json_str):driver_number::INTEGER, "
            "PARSE_JSON(json_str):lap_number::INTEGER"
        ),
        source_label=f"openf1/{season}/{round_num}/laps",
    )

    # Fetch and load stints
    stints = fetch_stints(session_key)
    _load_records_to_raw(
        records=stints,
        table_name="stints",
        season=season,
        round_num=round_num,
        unique_keys=["session_key", "driver_number", "stint_number"],
        extra_cols="session_key, driver_number, stint_number",
        extra_vals=(
            "PARSE_JSON(json_str):session_key::INTEGER, "
            "PARSE_JSON(json_str):driver_number::INTEGER, "
            "PARSE_JSON(json_str):stint_number::INTEGER"
        ),
        source_label=f"openf1/{season}/{round_num}/stints",
    )

    # Fetch and load pit stops
    pits = fetch_pit_stops(session_key)
    _load_records_to_raw(
        records=pits,
        table_name="pit_stops",
        season=season,
        round_num=round_num,
        unique_keys=["session_key", "driver_number", "lap_number"],
        extra_cols="session_key, driver_number, lap_number",
        extra_vals=(
            "PARSE_JSON(json_str):session_key::INTEGER, "
            "PARSE_JSON(json_str):driver_number::INTEGER, "
            "PARSE_JSON(json_str):lap_number::INTEGER"
        ),
        source_label=f"openf1/{season}/{round_num}/pit_stops",
    )


# ─── dbt run ─────────────────────────────────────────────────────────────────

def run_dbt(**context):
    """Run dbt from the dbt/ directory."""
    import subprocess
    dbt_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "dbt")
    result = subprocess.run(
        ["dbt", "run", "--profiles-dir", dbt_dir, "--project-dir", dbt_dir],
        capture_output=True, text=True,
    )
    logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise RuntimeError(f"dbt run failed: {result.stderr}")


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
    description="F1 API → Snowflake → dbt → Evidence rebuild",
    schedule="0 6 * * 1",  # Weekly on Monday 6am UTC during season
    start_date=datetime(2024, 1, 1),
    catchup=False,
    params={
        "season": Param(default="2024", type="string", description="F1 season year"),
        "round": Param(default="1", type="string", description="Round number"),
    },
    tags=["f1", "rivalry"],
) as dag:

    # Jolpica: fetch + load (parallel)
    t_qualifying = PythonOperator(task_id="ingest_qualifying", python_callable=ingest_qualifying)
    t_results = PythonOperator(task_id="ingest_results", python_callable=ingest_results)
    t_standings = PythonOperator(task_id="ingest_standings", python_callable=ingest_standings)

    # OpenF1: fetch + load (all in one task — sessions first, then laps/stints/pits)
    t_openf1 = PythonOperator(task_id="ingest_openf1", python_callable=ingest_openf1_data)

    # dbt
    t_dbt = PythonOperator(task_id="dbt_run", python_callable=run_dbt)

    # Evidence rebuild
    t_evidence = PythonOperator(task_id="trigger_evidence_build", python_callable=trigger_evidence_build)

    # Dependencies: all ingestion → dbt → Evidence
    [t_qualifying, t_results, t_standings, t_openf1] >> t_dbt >> t_evidence
