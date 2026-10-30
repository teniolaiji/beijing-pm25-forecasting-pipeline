# Beijing PM2.5 Time-Series Pipeline

Forecasting next-hour PM2.5 air pollution in Beijing from recent pollution levels and weather, with the data stored in MySQL and MongoDB, served through a CRUD API, and fed into a prediction script.

## Dataset

Beijing PM2.5 (US Embassy readings + Beijing Capital Airport weather), hourly, 1 Jan 2010 to 31 Dec 2014, 43,824 rows.

- **Downloaded from:** [Kaggle: Beijing PM2.5 Data Data Set](https://www.kaggle.com/datasets/djhavera/beijing-pm25-data-data-set) (original file `PRSA_data_2010.1.1-2014.12.31.csv`, saved here as `data/raw/beijing_pm25.csv`)
- **Original source:** [UCI Machine Learning Repository: Beijing PM2.5](https://archive.ics.uci.edu/dataset/381/beijing+pm2+5+data), CC BY 4.0
- **Paper:** Liang, X. et al. (2015). Assessing Beijing's PM2.5 pollution: severity, weather impact, APEC and winter heating. *Proceedings of the Royal Society A*, 471(2182).

| Clean column | Raw column | Meaning |
|---|---|---|
| `datetime` | year, month, day, hour | Timestamp (hourly) |
| `pm25` | pm2.5 | **Target**: PM2.5 concentration (ug/m³) |
| `dew_point` | DEWP | Dew point (°C) |
| `temperature` | TEMP | Temperature (°C) |
| `pressure` | PRES | Air pressure (hPa) |
| `wind_dir` | cbwd | Combined wind direction (NW, NE, SE, cv = calm/variable) |
| `wind_speed` | Iws | Cumulated wind speed (m/s) |
| `hours_snow` | Is | Cumulated hours of snow |
| `hours_rain` | Ir | Cumulated hours of rain |

Always load data with `src/load_data.py` so everyone uses these names.

## Repo structure

```
data/raw/          original CSV
notebooks/         EDA and modelling notebooks (Task 1)
src/               shared Python code (loading, preprocessing)
database/sql/      MySQL schema, load script, queries (Task 2)
database/mongo/    MongoDB design, load script, queries (Task 2)
api/               CRUD API for both databases (Task 3)
scripts/           prediction script (Task 4)
models/            saved trained model
outputs/figures/   saved plots for the report
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/load_data.py     # quick check that the data loads
```

## Reproduce the whole pipeline

Run everything from the repo root.

**1. Notebooks (Task 1).** Open `notebooks/01_eda.ipynb` and then `notebooks/02_modelling.ipynb`. The modelling notebook saves `models/pm25_xgb.joblib` and `models/model_meta.json`.

**2. Databases (Task 2).** You need MySQL and MongoDB running locally. Copy `.env.example` to `.env` and set your MySQL password.
```bash
mysql -u root -p < database/sql/schema.sql
python database/sql/load_mysql.py
python database/mongo/load_mongo.py
```
The queries and their results are in `database/sql/queries.sql` (screenshots in `database/sql/screenshots/`) and `database/mongo/queries.js`.

**3. API (Task 3).**
```bash
uvicorn api.main:app --reload
```
Open http://127.0.0.1:8000/docs to try every endpoint in the browser. Swap `sql` for `mongo` in any path to use MongoDB:

| Method | Path | What it does |
|---|---|---|
| POST | `/sql/records` | Add one hour (409 if that hour already exists) |
| GET | `/sql/records/{datetime}` | Get one hour, e.g. `/sql/records/2014-12-31T23:00:00` |
| PUT | `/sql/records/{datetime}` | Update only the fields sent, e.g. `{"pm25": 18}` |
| DELETE | `/sql/records/{datetime}` | Delete one hour |
| GET | `/sql/records/latest` | Most recent hour |
| GET | `/sql/records?start=...&end=...&limit=1000` | All hours in a date range, oldest first |

Test every endpoint on both databases with `pytest -v tests/` (or `USE_MONGOMOCK=1 pytest -v tests/` if you have no MongoDB server).

**4. Forecast (Task 4).** With the API running:
```bash
python scripts/predict.py                             # next hour after the latest record (MySQL)
python scripts/predict.py --db mongo                  # same, from MongoDB
python scripts/predict.py --at 2014-02-23T20:00:00    # forecast a past hour and compare with the actual
```
The script fetches the last 48 hours from the API, cleans them with `src/preprocessing.py`, builds features with `src/features.py`, loads the saved model and prints the forecast.

## Team

| Member | Role | Main files |
|---|---|---|
| Harmony Niyongabo | Data & EDA (Task 1A, 1B) | `notebooks/01_eda.ipynb` |
| Keyla Nyacyesa Bineza | Modelling (Task 1C) | `notebooks/02_modelling.ipynb`, `src/features.py`, `src/preprocessing.py`, `models/` |
| T. Akimana | Databases (Task 2) | `database/sql/`, `database/mongo/` |
| Oluwaloseyitowi (Towi) Iji | API & integration (Task 3, 4) | `src/load_data.py`, `api/`, `scripts/predict.py`, `tests/` |
