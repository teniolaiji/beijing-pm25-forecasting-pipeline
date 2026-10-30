"""
End-to-end checks for every endpoint on both databases.

Needs both databases loaded (database/sql/load_mysql.py, database/mongo/load_mongo.py).
Run from the repo root:   pytest -v tests/
Without a MongoDB server: USE_MONGOMOCK=1 pytest -v tests/   (in-memory stand-in)

Tests use an hour in 2099 so they never touch the real 2010-2014 data.
"""

import os

import pytest
from fastapi.testclient import TestClient

from api.main import app

if os.getenv("USE_MONGOMOCK") == "1":
    # In-memory stand-in for MongoDB, filled the same way as database/mongo/load_mongo.py
    import mongomock
    import pymongo

    from api import mongo_db

    mongo_db._client = mongomock.MongoClient()
    pymongo.MongoClient = lambda *args, **kwargs: mongo_db._client
    import runpy
    from pathlib import Path

    runpy.run_path(str(Path(__file__).resolve().parents[1] / "database" / "mongo" / "load_mongo.py"),
                   run_name="__main__")

client = TestClient(app)
TS = "2099-01-01T00:00:00"
NEW = {"datetime": TS, "pm25": 15.0, "dew_point": -20, "temperature": -4, "pressure": 1034,
       "wind_dir": "NW", "wind_speed": 251.64, "hours_snow": 0, "hours_rain": 0}


@pytest.fixture(params=["sql", "mongo"])
def db(request):
    client.delete(f"/{request.param}/records/{TS}")  # clean slate
    yield request.param
    client.delete(f"/{request.param}/records/{TS}")


def test_crud_cycle(db):
    r = client.post(f"/{db}/records", json=NEW)
    assert r.status_code == 201 and r.json()["pm25"] == 15.0

    assert client.post(f"/{db}/records", json=NEW).status_code == 409  # duplicate hour
    assert client.get(f"/{db}/records/{TS}").json()["wind_dir"] == "NW"

    r = client.put(f"/{db}/records/{TS}", json={"pm25": 18, "wind_dir": "cv"})
    assert r.json()["pm25"] == 18 and r.json()["wind_dir"] == "cv"
    assert r.json()["temperature"] == -4  # untouched field kept

    assert client.delete(f"/{db}/records/{TS}").status_code == 204
    assert client.get(f"/{db}/records/{TS}").status_code == 404


def test_validation(db):
    assert client.post(f"/{db}/records", json={**NEW, "wind_dir": "XX"}).status_code == 422
    assert client.put(f"/{db}/records/2014-12-31T23:00:00", json={}).status_code == 400
    assert client.delete(f"/{db}/records/2099-06-01T00:00:00").status_code == 404


def test_latest(db):
    r = client.get(f"/{db}/records/latest")
    assert r.status_code == 200 and r.json()["datetime"] == "2014-12-31T23:00:00"


def test_date_range(db):
    r = client.get(f"/{db}/records", params={"start": "2014-12-31T00:00:00", "end": "2014-12-31T23:00:00"})
    rows = r.json()
    assert len(rows) == 24
    assert rows[0]["datetime"] < rows[-1]["datetime"]  # oldest first

    bad = client.get(f"/{db}/records", params={"start": "2014-12-31", "end": "2014-01-01"})
    assert bad.status_code == 400


def test_both_databases_agree():
    params = {"start": "2014-06-01T00:00:00", "end": "2014-06-02T00:00:00"}
    assert client.get("/sql/records", params=params).json() == client.get("/mongo/records", params=params).json()
