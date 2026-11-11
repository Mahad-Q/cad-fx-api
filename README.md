# cad-fx-api

A REST API that stores and serves USD/CAD exchange rate data from the Bank of Canada, built with Python, Flask, and SQLite.

## How it works

1. `load_data.py` pulls daily USD/CAD rates from the Bank of Canada Valet API, cleans them (skips missing values, converts types), and loads them into a local SQLite database.
2. `app.py` serves that data as JSON through a Flask API. Data is stored locally, so requests are fast and the Bank of Canada is only called when you refresh the data.

## Setup

```
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python load_data.py
python app.py
```

## Endpoints

| Endpoint | Description |
|---|---|
| `GET /rates/latest` | Most recent rate |
| `GET /rates?start=YYYY-MM-DD&end=YYYY-MM-DD` | All rates in a date range |
| `GET /stats?start=YYYY-MM-DD&end=YYYY-MM-DD` | Average, min, max, and percent change over a range |

Invalid or missing dates return `400`. A range with no data returns `404`.

### Example

```
GET /stats?start=2025-01-02&end=2025-01-07
```
```json
{
  "start": "2025-01-02",
  "end": "2025-01-07",
  "count": 3,
  "average": 1.41,
  "minimum": 1.4,
  "maximum": 1.42,
  "percent_change": 1.429
}
```

## Tests

```
python -m pytest
```

## Possible next steps

- Add the Bank of Canada policy rate as a second table and JOIN it to the exchange rate by date
- 30-day moving average using a SQL window function
- Chart page with Chart.js
