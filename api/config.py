"""Database settings, read from the .env file in the repo root (see .env.example).

Defaults match database/sql/load_mysql.py and database/mongo/load_mongo.py,
so if the loaders work on your machine, the API works with no extra setup.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

MYSQL = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DB", "beijing_pm25"),
}

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "beijing_pm25")
MONGO_COLLECTION = "readings"

# Cap on rows returned by one date-range request
MAX_RANGE_ROWS = 5000
