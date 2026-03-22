"""Standalone script — generate LLM season narratives and store in Snowflake.

Usage:
    python scripts/generate_narratives.py              # all pairings
    python scripts/generate_narratives.py --season 2024  # single season
    python scripts/generate_narratives.py --force        # regenerate even if cached

Requires: ANTHROPIC_API_KEY in .env (or environment)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import snowflake.connector
import anthropic

NARRATIVE_MODEL = "claude-sonnet-4-20250514"


def get_conn():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ.get("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        database=os.environ.get("SNOWFLAKE_DATABASE", "F1_ANALYTICS"),
        schema="RAW",
    )


def build_prompt(season, constructor_id, d1_code, d2_code, mart_data, season_complete):
    season_status = "COMPLETED season" if season_complete else "IN-PROGRESS season (not all rounds have been raced yet)"
    return f"""You are a punchy, insightful Formula 1 analyst writing a season rivalry recap.

Season: {season} — {season_status}
Team: {constructor_id}
Drivers: {d1_code} vs {d2_code}

DATA:
{json.dumps(mart_data, indent=2, default=str)}

Write a SHORT, structured HTML snippet (100-150 words max) summarizing this teammate rivalry.

Format EXACTLY like this — no other HTML tags, no wrapper, no markdown:

<p class="f1-narrative-hook">One punchy sentence summarizing the overall story of this rivalry.</p>
<div class="f1-narrative-bullets">
<div class="f1-narrative-item"><span class="f1-narrative-label">Qualifying</span> 1-2 sentences on quali battle</div>
<div class="f1-narrative-item"><span class="f1-narrative-label">Race Day</span> 1-2 sentences on race results/drama</div>
<div class="f1-narrative-item"><span class="f1-narrative-label">Key Moment</span> 1 sentence on the defining moment, DNF, or momentum shift</div>
<div class="f1-narrative-item"><span class="f1-narrative-label">Verdict</span> 1 sentence on who won the intra-team battle</div>
</div>

Rules:
- Use driver codes ({d1_code}/{d2_code}), not full names
- Write in third person ONLY — never use "you", "your", or second person
- If the season is IN-PROGRESS, use qualifiers like "so far", "through X rounds", "early signs suggest" — do NOT write as if the season is finished
- Tone: authoritative, entertaining, concise — like a TV analyst's summary card
- Output ONLY the HTML, nothing else — no markdown fences, no explanation"""


def query_mart_data(cur, season, constructor_id, d1_code, d2_code):
    mart_data = {}

    cur.execute("""
        SELECT * FROM RAW_ANALYTICS.MART_SEASON_SUMMARY
        WHERE season = %s AND constructor_id = %s
          AND driver_1_code = %s AND driver_2_code = %s
    """, (season, constructor_id, d1_code, d2_code))
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    mart_data["season_summary"] = [dict(zip(cols, row)) for row in rows]

    cur.execute("""
        SELECT round, round_label, driver_1_code, driver_2_code,
               faster_driver_code, gap_ms, both_set_time
        FROM RAW_ANALYTICS.MART_QUALIFYING_H2H
        WHERE season = %s AND constructor_id = %s
          AND driver_1_code = %s AND driver_2_code = %s
        ORDER BY round
    """, (season, constructor_id, d1_code, d2_code))
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    mart_data["qualifying_h2h"] = [dict(zip(cols, row)) for row in rows]

    cur.execute("""
        SELECT round, round_label, race_winner_code,
               driver_1_finish, driver_2_finish,
               driver_1_points, driver_2_points,
               driver_1_dnf_category, driver_2_dnf_category
        FROM RAW_ANALYTICS.MART_RACE_H2H
        WHERE season = %s AND constructor_id = %s
          AND driver_1_code = %s AND driver_2_code = %s
        ORDER BY round
    """, (season, constructor_id, d1_code, d2_code))
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    mart_data["race_h2h"] = [dict(zip(cols, row)) for row in rows]

    cur.execute("""
        SELECT driver_code, cumulative_points
        FROM RAW_ANALYTICS.MART_POINTS_TRAJECTORY
        WHERE season = %s AND driver_code IN (%s, %s)
        ORDER BY round DESC LIMIT 2
    """, (season, d1_code, d2_code))
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    mart_data["points_final"] = [dict(zip(cols, row)) for row in rows]

    cur.execute("""
        SELECT driver_code,
               ROUND(AVG(consistency_score), 1) AS avg_consistency,
               ROUND(AVG(median_lap_s), 3) AS avg_median_lap
        FROM RAW_ANALYTICS.MART_LAP_PACE_SUMMARY
        WHERE season = %s AND constructor_id = %s
          AND driver_code IN (%s, %s)
        GROUP BY driver_code
    """, (season, constructor_id, d1_code, d2_code))
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    mart_data["pace_summary"] = [dict(zip(cols, row)) for row in rows]

    return mart_data


def main():
    parser = argparse.ArgumentParser(description="Generate LLM season narratives")
    parser.add_argument("--season", type=int, help="Filter to a single season")
    parser.add_argument("--force", action="store_true", help="Regenerate even if cached")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set in .env or environment")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    conn = get_conn()
    cur = conn.cursor()

    try:
        # Get all pairings
        query = """
            SELECT DISTINCT season, constructor_id, driver_1_code, driver_2_code
            FROM RAW_ANALYTICS.MART_SEASON_SUMMARY
        """
        params = ()
        if args.season:
            query += " WHERE season = %s"
            params = (args.season,)
        query += " ORDER BY season, constructor_id"

        cur.execute(query, params)
        pairings = cur.fetchall()
        print(f"Found {len(pairings)} pairings to process\n")

        current_year = datetime.now().year
        generated = 0
        skipped = 0
        errors = 0

        for season, constructor_id, d1_code, d2_code in pairings:
            label = f"{season} {constructor_id} {d1_code}v{d2_code}"
            try:
                mart_data = query_mart_data(cur, season, constructor_id, d1_code, d2_code)
                season_complete = season < current_year
                prompt = build_prompt(season, constructor_id, d1_code, d2_code, mart_data, season_complete)
                prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()

                if not args.force:
                    cur.execute("""
                        SELECT prompt_hash FROM RAW.RAW_SEASON_NARRATIVES
                        WHERE season = %s AND constructor_id = %s
                          AND driver_1_code = %s AND driver_2_code = %s
                    """, (season, constructor_id, d1_code, d2_code))
                    existing = cur.fetchone()
                    if existing and existing[0] == prompt_hash:
                        print(f"  CACHED  {label}")
                        skipped += 1
                        continue

                print(f"  GENERATING  {label} ...", end=" ", flush=True)
                message = client.messages.create(
                    model=NARRATIVE_MODEL,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )
                narrative_text = message.content[0].text

                cur.execute("""
                    DELETE FROM RAW.RAW_SEASON_NARRATIVES
                    WHERE season = %s AND constructor_id = %s
                      AND driver_1_code = %s AND driver_2_code = %s
                """, (season, constructor_id, d1_code, d2_code))
                cur.execute("""
                    INSERT INTO RAW.RAW_SEASON_NARRATIVES
                        (season, constructor_id, driver_1_code, driver_2_code,
                         narrative_text, model_id, prompt_hash, generated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP())
                """, (season, constructor_id, d1_code, d2_code,
                      narrative_text, NARRATIVE_MODEL, prompt_hash))

                print(f"OK ({len(narrative_text)} chars)")
                generated += 1
                time.sleep(0.5)

            except Exception as e:
                print(f"  ERROR  {label}: {e}")
                errors += 1
                continue

        print(f"\nDone — {generated} generated, {skipped} cached, {errors} errors")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
