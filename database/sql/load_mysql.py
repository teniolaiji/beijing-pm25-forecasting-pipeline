"""
Load the Beijing PM2.5 data into the MySQL database `beijing_pm25`.

Tables are filled in this order (because of the foreign keys):
    1. wind_directions  (one row per wind code: NW, NE, SE, cv)
    2. weather_readings (one row per hour, points to wind_directions)
    3. pm25_readings    (one row per hour, points to weather_readings)

Run from the repo root:
    python database/sql/load_mysql.py
"""
import os
import sys
from pathlib import Path

import mysql.connector
import pandas as pd
from dotenv import load_dotenv

#Make `src/` importable so we can use the team's shared loader.
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))
from src.load_data import load_raw  # noqa: E402
load_dotenv(ROOT / ".env")  
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": os.getenv("MYSQL_PASSWORD", ""),  
    "database": "beijing_pm25",
}


def to_float(value):
    """Return a float or None when the value is missing (MySQL stores NULL)."""
    return None if pd.isna(value) else float(value)


def to_int(value):
    """Return an int or None when the value is missing (MySQL stores NULL)."""
    return None if pd.isna(value) else int(value)


def main():
    df = load_raw()
    print(f"Loaded {len(df):,} rows from the CSV")

    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Empty the tables first(children before parents) so the script can be re-run.
    for table in ("pm25_readings", "weather_readings", "wind_directions"):
        cur.execute(f"DELETE FROM {table}")

    # 1. Wind directions: insert each distinct code once.
    codes = df["wind_dir"].dropna().unique()
    cur.executemany(
        "INSERT INTO wind_directions (code) VALUES (%s)",
        [(code,) for code in codes],
    )
    cur.execute("SELECT code, wind_dir_id FROM wind_directions")
    wind_ids = dict(cur.fetchall())  # {"NW": 1, "NE": 2, ...}

    # 2. Weather readings: one row per hour.
    weather_rows = []
    for r in df.itertuples(index=False):
        weather_rows.append((
            r.datetime.to_pydatetime(),
            to_float(r.dew_point),
            to_float(r.temperature),
            to_float(r.pressure),
            wind_ids.get(r.wind_dir),  #None if the wind code is missing
            to_float(r.wind_speed),
            to_int(r.hours_snow),
            to_int(r.hours_rain),
        ))
    cur.executemany(
        """INSERT INTO weather_readings
           (reading_time, dew_point, temperature, pressure,
            wind_dir_id, wind_speed, hours_snow, hours_rain)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        weather_rows,
    )

    # 3. PM2.5 readings: link each value to its weather row through reading_time.
    cur.execute("SELECT reading_time, weather_id FROM weather_readings")
    weather_ids = dict(cur.fetchall())  #{datetime: weather_id}

    pm25_rows = [
        (weather_ids[r.datetime.to_pydatetime()], to_int(r.pm25))
        for r in df.itertuples(index=False)
    ]
    cur.executemany(
        "INSERT INTO pm25_readings (weather_id, pm25) VALUES (%s, %s)",
        pm25_rows,
    )

    conn.commit()

    #Check how many rows are in each table
    for table in ("wind_directions", "weather_readings", "pm25_readings"):
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"{table}: {cur.fetchone()[0]:,} rows")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()