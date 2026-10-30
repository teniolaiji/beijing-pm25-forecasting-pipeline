"""
MongoDB access for the design in database/mongo/load_mongo.py:
collection "readings", one document per hour:

    {"datetime": Date, "pm25": int | null,
     "weather": {"dew_point", "temperature", "pressure", "wind_dir",
                 "wind_speed", "hours_snow", "hours_rain"}}

The API speaks flat records, so this module flattens documents on the way
out and nests them on the way in.
"""

from pymongo import MongoClient

from api.config import MONGO_COLLECTION, MONGO_DB, MONGO_URI

WEATHER_FIELDS = ["dew_point", "temperature", "pressure", "wind_dir",
                  "wind_speed", "hours_snow", "hours_rain"]

_client = None


def collection():
    """One shared client for the whole app (pymongo pools connections itself)."""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client[MONGO_DB][MONGO_COLLECTION]


def to_document(rec: dict) -> dict:
    return {
        "datetime": rec["datetime"],
        "pm25": rec["pm25"],
        "weather": {f: rec[f] for f in WEATHER_FIELDS},
    }


def to_record(doc: dict) -> dict:
    return {"datetime": doc["datetime"], "pm25": doc.get("pm25"), **doc["weather"]}


def get_record(ts):
    doc = collection().find_one({"datetime": ts}, {"_id": 0})
    return to_record(doc) if doc else None


def create_record(rec: dict):
    collection().insert_one(to_document(rec))


def update_record(ts, changes: dict):
    """$set only the given fields, so the rest of the document is untouched."""
    update = {(k if k == "pm25" else f"weather.{k}"): v for k, v in changes.items()}
    return collection().update_one({"datetime": ts}, {"$set": update}).matched_count > 0


def delete_record(ts):
    return collection().delete_one({"datetime": ts}).deleted_count > 0
