"""Basic tests. Run: python -m pytest   (pip install pytest) or python test_app.py"""
import os
import tempfile

# Point the app at a temporary database BEFORE importing it
tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
tmp.close()
os.environ["RATES_DB"] = tmp.name

import load_data
import app as app_module

fake_api_response = [
    {"d": "2025-01-02", "FXUSDCAD": {"v": "1.4000"}},
    {"d": "2025-01-03", "FXUSDCAD": {"v": "1.4100"}},
    {"d": "2025-01-06", "FXUSDCAD": {"v": ""}},          # missing value, should be skipped
    {"d": "2025-01-07", "FXUSDCAD": {"v": "1.4200"}},
]
load_data.save(load_data.clean(fake_api_response), tmp.name)
client = app_module.app.test_client()


def test_clean_skips_missing():
    assert len(load_data.clean(fake_api_response)) == 3


def test_latest():
    data = client.get("/rates/latest").get_json()
    assert data == {"date": "2025-01-07", "usd_cad": 1.42}


def test_range():
    data = client.get("/rates?start=2025-01-02&end=2025-01-03").get_json()
    assert data["count"] == 2


def test_stats():
    data = client.get("/stats?start=2025-01-02&end=2025-01-07").get_json()
    assert data["count"] == 3
    assert data["minimum"] == 1.4 and data["maximum"] == 1.42
    assert data["percent_change"] == 1.429


def test_bad_date_is_400():
    assert client.get("/rates?start=banana&end=2025-01-03").status_code == 400
    assert client.get("/stats").status_code == 400


def test_empty_range_is_404():
    assert client.get("/stats?start=2020-01-01&end=2020-01-31").status_code == 404


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
