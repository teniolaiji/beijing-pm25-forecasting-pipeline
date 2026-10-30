"""
Load the Beijing PM2.5 data into MongoDB.
One document per hour, weather values inside a "weather" sub-document.

Run from the repo root:
    python database/mongo/load_mongo.py
"""

import sys
from pathlib import Path

import pandas as pd
from pymongo import MongoClient

#so python can find src/load_data.py(the team's shared loader)
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))
from src.load_data import load_raw  # noqa: E402

client = MongoClient("mongodb://localhost:27017")
collection = client["beijing_pm25"]["readings"]


def clean(value):
    #missing values (NaN) become None which Mongo saves as null
    if pd.isna(value):
        return None
    #numpy numbers are not accepted by pymongo so turn them into normal ones
    if hasattr(value, "item"):
        return value.item()
    return value


def main():
    df = load_raw()
    print(f"{len(df):,} rows read from the CSV")

    #start from an empty collection so I the script can be run again without duplicates
    collection.delete_many({})

    documents = []
    for r in df.itertuples(index=False):
        pm25 = clean(r.pm25)
        if pm25 is not None:
            pm25 = int(pm25)  #pandas makes it a float because of the NaNs

        documents.append({
            "datetime": r.datetime.to_pydatetime(),  #a real date not text
            "pm25": pm25,
            "weather": {
                "dew_point": clean(r.dew_point),
                "temperature": clean(r.temperature),
                "pressure": clean(r.pressure),
                "wind_dir": clean(r.wind_dir),
                "wind_speed": clean(r.wind_speed),
                "hours_snow": clean(r.hours_snow),
                "hours_rain": clean(r.hours_rain),
            },
        })

    #insert in chunks of 5000 instead of everything at once
    for i in range(0, len(documents), 5000):
        collection.insert_many(documents[i:i + 5000])

    #index on datetime so date range queries are fast(unique = one doc per hour)
    collection.create_index("datetime", unique=True)

    print(f"{collection.count_documents({}):,} documents saved in MongoDB")
    print(collection.find_one({"pm25": {"$ne": None}}, {"_id": 0}))

    client.close()


if __name__ == "__main__":
    main()
client.close()