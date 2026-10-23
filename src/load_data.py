"""
Load the raw Beijing PM2.5 CSV and give it clean, agreed column names.

This file is the team's "data contract". Every other part of the project
(EDA, model, databases, API, predict script) should read data through
load_raw() so we all use the same column names and the same timestamp.
"""

from pathlib import Path

import pandas as pd

RAW_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "beijing_pm25.csv"

# Raw name -> clean name. Short, lowercase, no dots (pm2.5 breaks SQL and Mongo).
COLUMN_MAP = {
    "pm2.5": "pm25",          # target: PM2.5 concentration (ug/m^3)
    "DEWP": "dew_point",      # dew point (deg C)
    "TEMP": "temperature",    # temperature (deg C)
    "PRES": "pressure",       # air pressure (hPa)
    "cbwd": "wind_dir",       # combined wind direction: NW, NE, SE, cv (calm/variable)
    "Iws": "wind_speed",      # cumulated wind speed (m/s)
    "Is": "hours_snow",       # cumulated hours of snow
    "Ir": "hours_rain",       # cumulated hours of rain
}


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    """Read the CSV, build a single datetime column, rename columns, sort by time."""
    df = pd.read_csv(path)

    # The raw file splits time across year/month/day/hour. Merge into one timestamp.
    df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]])

    df = df.rename(columns=COLUMN_MAP)
    df = df[["datetime", *COLUMN_MAP.values()]]

    return df.sort_values("datetime").reset_index(drop=True)


if __name__ == "__main__":
    data = load_raw()
    print(data.head())
    print(f"\n{len(data):,} rows from {data.datetime.min()} to {data.datetime.max()}")
