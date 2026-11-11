"""Flask REST API that serves USD/CAD exchange rates stored in SQLite.

Run:  python app.py   (after python load_data.py)
"""
import os
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, request

DB_PATH = os.environ.get("RATES_DB", "rates.db")

app = Flask(__name__)


def query_db(sql, params=()):
    """Run a SELECT and return rows as a list of dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def valid_date(text):
    """True if text is a real date in YYYY-MM-DD format."""
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def get_range():
    """Read and validate ?start= and ?end= from the URL. Returns (start, end, error_response)."""
    start = request.args.get("start")
    end = request.args.get("end")
    if not valid_date(start) or not valid_date(end):
        return None, None, (jsonify(error="start and end are required, format YYYY-MM-DD"), 400)
    if start > end:
        return None, None, (jsonify(error="start must not be after end"), 400)
    return start, end, None


@app.route("/rates/latest")
def latest():
    rows = query_db("SELECT date, usd_cad FROM rates ORDER BY date DESC LIMIT 1")
    if not rows:
        return jsonify(error="no data loaded, run load_data.py first"), 404
    return jsonify(rows[0])


@app.route("/rates")
def rates_in_range():
    start, end, error = get_range()
    if error:
        return error
    rows = query_db(
        "SELECT date, usd_cad FROM rates WHERE date BETWEEN ? AND ? ORDER BY date",
        (start, end),
    )
    return jsonify(start=start, end=end, count=len(rows), rates=rows)


@app.route("/stats")
def stats():
    start, end, error = get_range()
    if error:
        return error
    summary = query_db(
        "SELECT COUNT(*) AS count, AVG(usd_cad) AS average, "
        "MIN(usd_cad) AS minimum, MAX(usd_cad) AS maximum "
        "FROM rates WHERE date BETWEEN ? AND ?",
        (start, end),
    )[0]
    if summary["count"] == 0:
        return jsonify(error="no data in that range"), 404

    first = query_db(
        "SELECT usd_cad FROM rates WHERE date BETWEEN ? AND ? ORDER BY date ASC LIMIT 1",
        (start, end),
    )[0]["usd_cad"]
    last = query_db(
        "SELECT usd_cad FROM rates WHERE date BETWEEN ? AND ? ORDER BY date DESC LIMIT 1",
        (start, end),
    )[0]["usd_cad"]

    return jsonify(
        start=start,
        end=end,
        count=summary["count"],
        average=round(summary["average"], 4),
        minimum=summary["minimum"],
        maximum=summary["maximum"],
        percent_change=round((last - first) / first * 100, 3),  # (last - first) / first * 100
    )


if __name__ == "__main__":
    app.run(debug=True)
