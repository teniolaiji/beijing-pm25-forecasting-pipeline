"""
Task 4: forecast next hour's PM2.5 using data fetched from our API.

Steps
  1. Fetch the latest record, then the hours before it, from the API (MySQL or MongoDB)
  2. Preprocess them with the same clean() used in training
  3. Load the trained model and its metadata
  4. Build the feature row with features.next_hour_row() and forecast

Run from the repo root, with the API running (uvicorn api.main:app):
    python scripts/predict.py                                 # latest hour, MySQL
    python scripts/predict.py --db mongo                      # latest hour, MongoDB
    python scripts/predict.py --at 2014-02-26T12:00:00        # pretend it is that hour
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import joblib
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from features import FEATURE_COLUMNS, next_hour_row  # noqa: E402
from preprocessing import clean  # noqa: E402

MODEL_PATH = ROOT / "models" / "pm25_xgb.joblib"
META_PATH = ROOT / "models" / "model_meta.json"

# China's air quality bands for PM2.5 (ug/m3), used to label the forecast
AQI_BANDS = [(35, "Excellent"), (75, "Good"), (115, "Lightly polluted"),
             (150, "Moderately polluted"), (250, "Heavily polluted"), (float("inf"), "Severely polluted")]

# Extra hours fetched beyond what the model needs, so short gaps at the start
# of the window can still be interpolated by clean()
BUFFER_HOURS = 24


def get(url, **params):
    try:
        resp = requests.get(url, params=params, timeout=30)
    except requests.ConnectionError:
        sys.exit(f"Could not reach the API at {url}. Start it with: uvicorn api.main:app")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def fetch_history(api, db, end, hours):
    """Step 1: the `hours` hourly records up to and including `end`."""
    base = f"{api}/{db}/records"
    if end is None:
        latest = get(f"{base}/latest")
        if latest is None:
            sys.exit(f"The {db} database is empty")
        end = datetime.fromisoformat(latest["datetime"])

    start = end - timedelta(hours=hours - 1)
    records = get(base, start=start.isoformat(), end=end.isoformat(), limit=hours)
    if not records:
        sys.exit(f"No records between {start} and {end}")
    return pd.DataFrame(records), end


def preprocess(records, end, hours):
    """Step 2: same cleaning as training, on a complete hourly grid."""
    records["datetime"] = pd.to_datetime(records["datetime"])

    # If an hour was deleted through the API, put it back as an empty row so
    # "1 hour ago" still means exactly one hour ago
    grid = pd.date_range(end=end, periods=hours, freq="h", name="datetime")
    records = records.set_index("datetime").reindex(grid).reset_index()

    return clean(records)


def load_model():
    """Step 3: the saved model plus the metadata that says how to use it."""
    model = joblib.load(MODEL_PATH)
    meta = json.loads(META_PATH.read_text())
    if meta["features"] != FEATURE_COLUMNS:
        sys.exit("src/features.py no longer matches the saved model. Retrain the model.")
    return model, meta


def band(value):
    return next(label for limit, label in AQI_BANDS if value <= limit)


def main():
    parser = argparse.ArgumentParser(description="Forecast next hour's PM2.5 from the API")
    parser.add_argument("--api", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--db", choices=["sql", "mongo"], default="sql", help="which database to read")
    parser.add_argument("--at", type=datetime.fromisoformat, default=None,
                        help="forecast the hour after this one (default: the latest record)")
    args = parser.parse_args()

    model, meta = load_model()
    hours = meta["history_hours_needed"] + BUFFER_HOURS

    print(f"[1/4] Fetching {hours} hours from {args.api}/{args.db} ...")
    records, end = fetch_history(args.api, args.db, args.at, hours)
    print(f"      got {len(records)} records, {records.datetime.iloc[0]} to {records.datetime.iloc[-1]}")

    print("[2/4] Cleaning (interpolating PM2.5 gaps of 6 hours or less) ...")
    missing_before = int(records["pm25"].isna().sum())
    history = preprocess(records, end, hours)
    print(f"      missing PM2.5: {missing_before} before, {int(history.pm25.isna().sum())} after")

    print(f"[3/4] Loaded model {meta['model']} ({meta['experiment']}), "
          f"test RMSE {meta['test_metrics']['RMSE']:.2f} ug/m3")

    row = next_hour_row(history)
    change = float(model.predict(row[meta["features"]])[0])
    last = float(row["pm25_lag1"].iloc[0])
    forecast = max(0.0, last + change)
    target_time = row.index[0]

    print("[4/4] Forecast")
    print(f"      last reading  {end:%Y-%m-%d %H:%M}  {last:6.1f} ug/m3")
    print(f"      forecast      {target_time:%Y-%m-%d %H:%M}  {forecast:6.1f} ug/m3"
          f"  ({change:+.1f}, {band(forecast)})")

    # When forecasting the past (--at), show how close we got
    actual = get(f"{args.api}/{args.db}/records/{target_time.isoformat()}")
    if actual and actual.get("pm25") is not None:
        print(f"      actual        {target_time:%Y-%m-%d %H:%M}  {actual['pm25']:6.1f} ug/m3"
              f"  (error {forecast - actual['pm25']:+.1f})")


if __name__ == "__main__":
    main()
