"""Fetch USD/CAD daily exchange rates from the Bank of Canada and store them in SQLite.

Run:  python load_data.py
Safe to re-run: existing dates are overwritten, not duplicated.
"""
import sqlite3
import requests

DB_PATH = "rates.db"
URL = "https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json"
SERIES = "FXUSDCAD"
START_DATE = "2023-01-01"


def fetch_observations(start_date=START_DATE):
    """Download raw observations from the Bank of Canada Valet API."""
    response = requests.get(URL, params={"start_date": start_date}, timeout=15)
    response.raise_for_status()  # raises an error on 4xx/5xx instead of failing silently
    return response.json()["observations"]


def clean(observations):
    """Turn raw API records into (date, rate) tuples, skipping missing or bad values."""
    rows = []
    for obs in observations:
        value = obs.get(SERIES, {}).get("v")  # the rate is nested: {"d": date, "FXUSDCAD": {"v": "1.35"}}
        if value in (None, ""):
            continue  # no rate published that day
        try:
            rows.append((obs["d"], float(value)))  # the API returns rates as strings, so convert
        except (ValueError, KeyError):
            continue  # skip anything malformed
    return rows


def save(rows, db_path=DB_PATH):
    """Create the table if needed and insert the rows."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS rates ("
        "date TEXT PRIMARY KEY, "  # PRIMARY KEY: one row per date, no duplicates
        "usd_cad REAL NOT NULL)"
    )
    # ? placeholders keep data separate from the SQL text (prevents SQL injection)
    conn.executemany("INSERT OR REPLACE INTO rates (date, usd_cad) VALUES (?, ?)", rows)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    raw = fetch_observations()
    rows = clean(raw)
    save(rows)
    print(f"Fetched {len(raw)} records, saved {len(rows)} clean rows to {DB_PATH}")
