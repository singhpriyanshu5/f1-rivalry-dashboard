"""Standalone ingestion script — load a single round from APIs into Snowflake.

Usage: python scripts/ingest_round.py [season] [round]
Default: 2024 round 1

All data comes from Jolpica (Ergast-compatible API).
Each table stores the full API response array as one VARIANT row per (season, round).
DELETE+INSERT for idempotency.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "airflow", "dags"))

import snowflake.connector
from utils.jolpica_client import (
    fetch_qualifying, fetch_results, fetch_sprint_results,
    fetch_driver_standings, fetch_laps, fetch_pit_stops, fetch_schedule,
)


def get_conn():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role="ACCOUNTADMIN",
        warehouse="COMPUTE_WH",
        database="F1_ANALYTICS",
        schema="RAW",
    )


def load_jolpica_array(records, table_name, season, round_num):
    """Store entire API response array as one VARIANT row per (season, round)."""
    if not records:
        print(f"  No records for {table_name}")
        return

    conn = get_conn()
    cur = conn.cursor()
    raw_table = f"RAW.RAW_{table_name.upper()}"
    source_label = f"jolpica/{season}/{round_num}/{table_name}"

    try:
        # Delete existing row for this season/round (idempotent)
        cur.execute(f"DELETE FROM {raw_table} WHERE season = %s AND round = %s", (season, round_num))

        # Insert as VARCHAR temp, then INSERT...SELECT with PARSE_JSON
        cur.execute("CREATE TEMPORARY TABLE _tmp_jolpica (json_str VARCHAR)")
        cur.execute(
            "INSERT INTO _tmp_jolpica (json_str) VALUES (%s)",
            (json.dumps(records, default=str),)
        )
        cur.execute(f"""
            INSERT INTO {raw_table} (raw_data, season, round, _ingested_at, _source_file)
            SELECT PARSE_JSON(json_str), {season}, {round_num}, CURRENT_TIMESTAMP(), '{source_label}'
            FROM _tmp_jolpica
        """)
        cur.execute("DROP TABLE _tmp_jolpica")
        print(f"  Loaded {len(records)} records (1 row) into {raw_table}")
    finally:
        cur.close()
        conn.close()


def ingest_round(season, round_num):
    print(f"1/7 Qualifying ({season} R{round_num})...")
    data = fetch_qualifying(season, round_num)
    print(f"  Fetched {len(data)} records")
    load_jolpica_array(data, "qualifying", season, round_num)

    print("2/7 Results...")
    data = fetch_results(season, round_num)
    print(f"  Fetched {len(data)} records")
    load_jolpica_array(data, "results", season, round_num)

    print("3/7 Sprint results...")
    data = fetch_sprint_results(season, round_num)
    print(f"  Fetched {len(data)} records")
    load_jolpica_array(data, "sprint_results", season, round_num)

    print("4/7 Standings...")
    data = fetch_driver_standings(season, round_num)
    print(f"  Fetched {len(data)} records")
    load_jolpica_array(data, "driver_standings", season, round_num)

    print("5/7 Laps...")
    data = fetch_laps(season, round_num)
    print(f"  Fetched {len(data)} timing entries")
    load_jolpica_array(data, "jolpica_laps", season, round_num)

    print("6/7 Pit stops...")
    data = fetch_pit_stops(season, round_num)
    print(f"  Fetched {len(data)} records")
    load_jolpica_array(data, "jolpica_pit_stops", season, round_num)

    print("7/7 Schedule...")
    races = fetch_schedule(season)
    print(f"  Fetched {len(races)} races")
    load_jolpica_array(races, "schedule", season, round_num=0)

    print(f"\nDone — {season} Round {round_num} loaded into Snowflake.")


if __name__ == "__main__":
    season = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    round_num = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    ingest_round(season, round_num)
