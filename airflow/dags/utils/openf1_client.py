"""OpenF1 API client with throttling."""

from __future__ import annotations

import time
import logging
from typing import Optional

import requests

BASE_URL = "https://api.openf1.org/v1"
REQUEST_DELAY = 0.3

logger = logging.getLogger(__name__)


def _get(url: str, params: Optional[dict] = None) -> list:
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    time.sleep(REQUEST_DELAY)
    return resp.json()


def fetch_race_sessions(season: int) -> list[dict]:
    """Fetch all Race sessions for a season, sorted by date."""
    sessions = _get(f"{BASE_URL}/sessions", {
        "year": season,
        "session_name": "Race",
    })
    sessions.sort(key=lambda s: s["date_start"])
    # Add derived round number (1-indexed, by date order)
    for i, session in enumerate(sessions, start=1):
        session["derived_round"] = i
    return sessions


def fetch_laps(session_key: int) -> list[dict]:
    """Fetch all laps for a session."""
    return _get(f"{BASE_URL}/laps", {"session_key": session_key})


def fetch_stints(session_key: int) -> list[dict]:
    """Fetch all stints for a session."""
    return _get(f"{BASE_URL}/stints", {"session_key": session_key})


def fetch_pit_stops(session_key: int) -> list[dict]:
    """Fetch all pit stops for a session."""
    return _get(f"{BASE_URL}/pit", {"session_key": session_key})
