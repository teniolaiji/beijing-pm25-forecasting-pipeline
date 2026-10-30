"""
Feature engineering for next-hour PM2.5 forecasting.

One row per TARGET hour t. Every feature uses only information available at the
end of hour t-1, so the model never sees the value it is trying to predict:

    lags            PM2.5 at t-1, t-2, t-3 and t-24
    rolling means   mean PM2.5 over the 6 and 24 hours before t
    weather         weather readings at t-1
    wind direction  one-hot wind direction at t-1
    calendar        hour, month and day of week of t

The same functions are used for training (training_table) and by
scripts/predict.py (next_hour_row).
"""

import pandas as pd

LAGS = [1, 2, 3, 24]
ROLL_WINDOWS = [6, 24]
WEATHER = ["dew_point", "temperature", "pressure", "wind_speed", "hours_snow", "hours_rain"]
WIND_DIRS = ["NE", "NW", "SE", "cv"]

FEATURE_COLUMNS = (
    [f"pm25_lag{k}" for k in LAGS]
    + [f"pm25_roll{w}" for w in ROLL_WINDOWS]
    + [f"{c}_lag1" for c in WEATHER]
    + [f"wind_{d}" for d in WIND_DIRS]
    + ["hour", "month", "dayofweek"]
)

# Hours of history needed before the target hour: lag 24 reaches back to t-24.
HISTORY_HOURS = max(max(LAGS), max(ROLL_WINDOWS))


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Feature table for every hour in df (df = output of preprocessing.clean)."""
    pm = df["pm25"]
    past = pm.shift(1)  # everything below looks back from t-1

    feats = pd.DataFrame(index=df.index)
    for k in LAGS:
        feats[f"pm25_lag{k}"] = pm.shift(k)
    for w in ROLL_WINDOWS:
        # min_periods=w: a window with a gap gives NaN instead of a misleading mean
        feats[f"pm25_roll{w}"] = past.rolling(w, min_periods=w).mean()
    for c in WEATHER:
        feats[f"{c}_lag1"] = df[c].shift(1)

    wind_prev = df["wind_dir"].shift(1)
    for d in WIND_DIRS:
        # Fixed list of directions, so a short history still gets all 4 columns
        feats[f"wind_{d}"] = (wind_prev == d).astype(float).where(wind_prev.notna())

    feats["hour"] = df.index.hour
    feats["month"] = df.index.month
    feats["dayofweek"] = df.index.dayofweek
    return feats[FEATURE_COLUMNS]


def training_table(df: pd.DataFrame, observed: pd.Series | None = None) -> pd.DataFrame:
    """Features plus `target` (PM2.5 at t), keeping only complete rows.

    observed: optional True/False per hour, True where PM2.5 was really measured.
    When given, hours whose target was filled in by interpolation are dropped,
    so the model is trained and scored only against real readings.
    """
    table = build_features(df)
    table["target"] = df["pm25"]
    if observed is not None:
        table = table[observed.reindex(table.index).fillna(False).astype(bool)]
    return table.dropna()


def next_hour_row(history: pd.DataFrame) -> pd.DataFrame:
    """One feature row for the hour after the end of `history`.

    history: cleaned hourly data (datetime index), at least HISTORY_HOURS long,
    ending at the latest known hour.
    """
    if len(history) < HISTORY_HOURS:
        raise ValueError(f"Need at least {HISTORY_HOURS} hours of history, got {len(history)}")

    history = history.sort_index()
    next_time = history.index[-1] + pd.Timedelta(hours=1)
    extended = pd.concat([history, pd.DataFrame(index=[next_time])])
    row = build_features(extended).iloc[[-1]]

    if row.isna().any(axis=None):
        gaps = row.columns[row.isna().iloc[0]].tolist()
        raise ValueError(f"Cannot forecast {next_time}: missing inputs {gaps}")
    return row
