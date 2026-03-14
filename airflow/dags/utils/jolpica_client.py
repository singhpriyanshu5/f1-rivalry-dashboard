"""Jolpica (Ergast) F1 API client with rate limiting."""

from __future__ import annotations

import time
import logging
import requests

BASE_URL = "https://api.jolpi.ca/ergast/f1"
REQUEST_DELAY = 0.5  # seconds between requests (stays under 200 req/hr)
MAX_RETRIES = 3

logger = logging.getLogger(__name__)


def _get(url: str) -> dict:
    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            time.sleep(REQUEST_DELAY)
            return resp.json()
        if resp.status_code == 429:
            wait = 2 ** attempt
            logger.warning(f"Rate limited (429). Retrying in {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
    raise RuntimeError(f"Failed after {MAX_RETRIES} retries: {url}")


def fetch_qualifying(season: int, round_num: int) -> list[dict]:
    """Fetch qualifying results for a specific race."""
    url = f"{BASE_URL}/{season}/{round_num}/qualifying.json"
    data = _get(url)
    races = data["MRData"]["RaceTable"]["Races"]
    if not races:
        return []
    return races[0]["QualifyingResults"]


def fetch_results(season: int, round_num: int) -> list[dict]:
    """Fetch race results for a specific race."""
    url = f"{BASE_URL}/{season}/{round_num}/results.json"
    data = _get(url)
    races = data["MRData"]["RaceTable"]["Races"]
    if not races:
        return []
    return races[0]["Results"]


def fetch_driver_standings(season: int, round_num: int) -> list[dict]:
    """Fetch driver standings after a specific round."""
    url = f"{BASE_URL}/{season}/{round_num}/driverStandings.json"
    data = _get(url)
    standings_table = data["MRData"]["StandingsTable"]["StandingsLists"]
    if not standings_table:
        return []
    return standings_table[0]["DriverStandings"]


def fetch_laps(season: int, round_num: int) -> list[dict]:
    """Fetch all lap timing data for a race (paginated, 100 entries per page)."""
    all_timings = []
    offset = 0
    limit = 100
    while True:
        url = f"{BASE_URL}/{season}/{round_num}/laps.json?limit={limit}&offset={offset}"
        data = _get(url)
        races = data["MRData"]["RaceTable"]["Races"]
        if not races:
            break
        laps = races[0].get("Laps", [])
        if not laps:
            break
        for lap in laps:
            lap_num = int(lap["number"])
            for timing in lap["Timings"]:
                all_timings.append({
                    "lap_number": lap_num,
                    "driver_id": timing["driverId"],
                    "position": int(timing["position"]) if "position" in timing else None,
                    "time": timing.get("time"),
                })
        total = int(data["MRData"]["total"])
        offset += limit
        if offset >= total:
            break
    return all_timings


def fetch_pit_stops(season: int, round_num: int) -> list[dict]:
    """Fetch all pit stop data for a race."""
    url = f"{BASE_URL}/{season}/{round_num}/pitstops.json?limit=100"
    data = _get(url)
    races = data["MRData"]["RaceTable"]["Races"]
    if not races:
        return []
    return races[0].get("PitStops", [])


def fetch_schedule(season: int) -> list[dict]:
    """Fetch the full race schedule for a season (to know total rounds)."""
    url = f"{BASE_URL}/{season}.json"
    data = _get(url)
    return data["MRData"]["RaceTable"]["Races"]
