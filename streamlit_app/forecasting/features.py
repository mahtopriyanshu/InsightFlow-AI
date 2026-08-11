"""Leakage-safe time-series feature construction."""
import pandas as pd


def lag_features(series: pd.Series) -> pd.DataFrame:
    values = pd.to_numeric(series, errors="coerce")
    frame = pd.DataFrame({"target": values})
    for lag in (1, 2, 3):
        frame[f"lag_{lag}"] = values.shift(lag)
    prior = values.shift(1)
    frame["rolling_mean_3"] = prior.rolling(3).mean()
    frame["rolling_std_3"] = prior.rolling(3).std(ddof=0)
    frame["time_index"] = range(len(frame))
    if isinstance(series.index, pd.DatetimeIndex):
        frame["month"] = series.index.month
        frame["quarter"] = series.index.quarter
    return frame
