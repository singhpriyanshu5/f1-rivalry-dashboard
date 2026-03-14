"""Batch ingestion — load all rounds for a season sequentially.

Usage: python scripts/ingest_season.py [season] [start_round]
Default: 2025 season, starting from round 1

Runs rounds sequentially with 2s delay to avoid Jolpica 429 rate limits.
"""

from __future__ import annotations

import sys
import time

from ingest_round import ingest_round


if __name__ == "__main__":
    season = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    start_round = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    end_round = int(sys.argv[3]) if len(sys.argv) > 3 else 24

    print(f"=== Ingesting {season} season: rounds {start_round}–{end_round} ===\n")

    failed = []
    for r in range(start_round, end_round + 1):
        print(f"\n{'='*50}")
        print(f"  ROUND {r} of {end_round}")
        print(f"{'='*50}")
        try:
            ingest_round(season, r)
        except Exception as e:
            print(f"  ERROR on round {r}: {e}")
            failed.append(r)

        if r < end_round:
            print("  Waiting 2s before next round...")
            time.sleep(2)

    print(f"\n{'='*50}")
    print(f"  SEASON {season} INGESTION COMPLETE")
    print(f"{'='*50}")
    if failed:
        print(f"  Failed rounds: {failed}")
        print(f"  Re-run with: python scripts/ingest_season.py {season} <round>")
    else:
        print(f"  All {end_round - start_round + 1} rounds loaded successfully.")
