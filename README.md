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

## Team

| Member | Role |
|---|---|
| TBD | Data & EDA (Task 1A, 1B) |
| TBD | Modelling (Task 1C) |
| TBD | Databases (Task 2) |
| Tee | API & integration (Task 3, 4) |
