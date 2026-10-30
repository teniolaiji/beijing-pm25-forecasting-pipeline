"""
Clean the hourly data (Shared by the model and predict.py).

Implements the cleaning rule chosen in Harmony's EDA (notebooks/01_eda.ipynb,
section 4): PM2.5 gaps of 6 hours or less are filled by linear interpolation;
longer gaps stay empty, because a straight line across a long outage would
invent pollution values.

Used by notebooks/01_eda.ipynb, /02_modelling.ipynb and scripts/predict.py.
"""

import pandas as pd

MAX_GAP_HOURS = 6


def clean(raw: pd.DataFrame, max_gap: int = MAX_GAP_HOURS) -> pd.DataFrame:
    """Return the data indexed by datetime, with short PM2.5 gaps filled."""
    df = raw.set_index("datetime").sort_index()

    pm = df["pm25"]
    missing = pm.isna()

    # Label each run of consecutive missing hours and measure its length.
    run_id = (missing != missing.shift()).cumsum()
    run_length = missing.groupby(run_id).transform("sum")
    short_gap = missing & (run_length <= max_gap)

    # Interpolate only between real readings (limit_area="inside"), then keep
    # the filled values for short gaps only.
    filled = pm.interpolate(method="linear", limit_area="inside")
    df["pm25"] = pm.where(~short_gap, filled)
    return df


if __name__ == "__main__":
    from load_data import load_raw

    raw = load_raw()
    df = clean(raw)
    print(f"Missing PM2.5 before: {raw.pm25.isna().sum():,}, after: {df.pm25.isna().sum():,}")
