"""Quick connectivity check for Jolpica and OpenF1 APIs."""

import requests
import sys


def test_jolpica():
    """Test Jolpica F1 API — fetch 2024 Round 1 qualifying."""
    url = "https://api.jolpi.ca/ergast/f1/2024/1/qualifying.json"
    resp = requests.get(url, timeout=15)
    data = resp.json()
    qualifiers = data["MRData"]["RaceTable"]["Races"]
    print(f"Jolpica API: {resp.status_code} — {len(qualifiers)} race(s) returned")
    return resp.status_code == 200


def test_openf1():
    """Test OpenF1 API — fetch 2024 race sessions."""
    url = "https://api.openf1.org/v1/sessions?year=2024&session_name=Race"
    resp = requests.get(url, timeout=15)
    sessions = resp.json()
    print(f"OpenF1 API:  {resp.status_code} — {len(sessions)} race session(s) returned")
    return resp.status_code == 200


if __name__ == "__main__":
    print("Testing F1 API connectivity...\n")
    jolpica_ok = test_jolpica()
    openf1_ok = test_openf1()
    print()
    if jolpica_ok and openf1_ok:
        print("All APIs reachable.")
    else:
        print("ERROR: One or more APIs failed.", file=sys.stderr)
        sys.exit(1)
