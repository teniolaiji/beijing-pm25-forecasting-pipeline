"""
MySQL access for the schema in database/sql/schema.sql:

    wind_directions (wind_dir_id, code)
    weather_readings (weather_id, reading_time, ..., wind_dir_id)
    pm25_readings    (pm25_id, weather_id, pm25)

The API speaks flat records, so this module joins the three tables on the
way out and splits a record across them on the way in.
"""

from contextlib import contextmanager

import mysql.connector

from api.config import MYSQL

IntegrityError = mysql.connector.errors.IntegrityError

# One query that rebuilds a flat record from the three tables
SELECT_RECORD = """
    SELECT w.reading_time AS datetime, p.pm25, w.dew_point, w.temperature, w.pressure,
           d.code AS wind_dir, w.wind_speed, w.hours_snow, w.hours_rain
    FROM weather_readings w
    LEFT JOIN wind_directions d ON d.wind_dir_id = w.wind_dir_id
    LEFT JOIN pm25_readings p ON p.weather_id = w.weather_id
"""

WEATHER_FIELDS = ["dew_point", "temperature", "pressure", "wind_speed", "hours_snow", "hours_rain"]


@contextmanager
def connection():
    """Open a connection, commit if everything worked, roll back if not."""
    conn = mysql.connector.connect(**MYSQL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _cursor(conn):
    return conn.cursor(dictionary=True)


def _wind_id(cur, code):
    cur.execute("SELECT wind_dir_id FROM wind_directions WHERE code = %s", (code,))
    row = cur.fetchone()
    return row["wind_dir_id"] if row else None


def _weather_id(cur, ts):
    cur.execute("SELECT weather_id FROM weather_readings WHERE reading_time = %s", (ts,))
    row = cur.fetchone()
    return row["weather_id"] if row else None


def get_record(ts):
    with connection() as conn:
        cur = _cursor(conn)
        cur.execute(SELECT_RECORD + " WHERE w.reading_time = %s", (ts,))
        return cur.fetchone()


def get_latest():
    with connection() as conn:
        cur = _cursor(conn)
        cur.execute(SELECT_RECORD + " ORDER BY w.reading_time DESC LIMIT 1")
        return cur.fetchone()


def get_range(start, end, limit):
    """Records with start <= datetime <= end, oldest first."""
    with connection() as conn:
        cur = _cursor(conn)
        cur.execute(
            SELECT_RECORD + " WHERE w.reading_time BETWEEN %s AND %s ORDER BY w.reading_time LIMIT %s",
            (start, end, limit),
        )
        return cur.fetchall()


def create_record(rec: dict):
    """Insert the weather row, then the PM2.5 row linked to it, in one transaction."""
    with connection() as conn:
        cur = _cursor(conn)
        cur.execute(
            """INSERT INTO weather_readings
               (reading_time, dew_point, temperature, pressure, wind_dir_id,
                wind_speed, hours_snow, hours_rain)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (rec["datetime"], rec["dew_point"], rec["temperature"], rec["pressure"],
             _wind_id(cur, rec["wind_dir"]), rec["wind_speed"], rec["hours_snow"], rec["hours_rain"]),
        )
        cur.execute(
            "INSERT INTO pm25_readings (weather_id, pm25) VALUES (%s, %s)",
            (cur.lastrowid, rec["pm25"]),
        )


def update_record(ts, changes: dict):
    """Update only the fields given. Returns False if the hour doesn't exist."""
    with connection() as conn:
        cur = _cursor(conn)
        weather_id = _weather_id(cur, ts)
        if weather_id is None:
            return False

        weather = {k: v for k, v in changes.items() if k in WEATHER_FIELDS}
        if "wind_dir" in changes:
            weather["wind_dir_id"] = _wind_id(cur, changes["wind_dir"])
        if weather:
            # Column names come from our own fixed list, never from the user
            sets = ", ".join(f"{col} = %s" for col in weather)
            cur.execute(f"UPDATE weather_readings SET {sets} WHERE weather_id = %s",
                        (*weather.values(), weather_id))

        if "pm25" in changes:
            # weather_id is UNIQUE in pm25_readings, so this inserts or overwrites
            cur.execute(
                """INSERT INTO pm25_readings (weather_id, pm25) VALUES (%s, %s)
                   ON DUPLICATE KEY UPDATE pm25 = VALUES(pm25)""",
                (weather_id, changes["pm25"]),
            )
        return True


def delete_record(ts):
    """Delete the PM2.5 row first (it points at the weather row), then the weather row."""
    with connection() as conn:
        cur = _cursor(conn)
        weather_id = _weather_id(cur, ts)
        if weather_id is None:
            return False
        cur.execute("DELETE FROM pm25_readings WHERE weather_id = %s", (weather_id,))
        cur.execute("DELETE FROM weather_readings WHERE weather_id = %s", (weather_id,))
        return True
