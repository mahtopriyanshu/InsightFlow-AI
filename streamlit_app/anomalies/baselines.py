"""Robust rolling historical baseline calculations."""
import numpy as np
import pandas as pd

from streamlit_app.anomalies.config import MIN_HISTORY,ROLLING_WINDOW

def complete_months(frame:pd.DataFrame,date_column:str="month")->pd.DataFrame:
    """Exclude months not covering calendar day 1 through month end."""
    data=frame.copy();data[date_column]=pd.to_datetime(data[date_column])
    if "first_day" in data and "last_day" in data:
        first=pd.to_datetime(data.first_day);last=pd.to_datetime(data.last_day)
        mask=(first.dt.day.eq(1))&(last.dt.day.eq(last.dt.days_in_month))
        data=data.loc[mask]
    return data.sort_values(date_column).reset_index(drop=True)

def rolling_baselines(series:pd.Series,window:int=ROLLING_WINDOW,min_history:int=MIN_HISTORY)->pd.DataFrame:
    """Calculate trailing median, MAD, IQR, and history count without leakage."""
    values=pd.to_numeric(series,errors="coerce")
    rows=[]
    for position,value in enumerate(values):
        history=values.iloc[max(0,position-window):position].dropna()
        if len(history)<min_history:
            rows.append((np.nan,np.nan,np.nan,len(history)));continue
        median=float(history.median());mad=float((history-median).abs().median())
        iqr=float(history.quantile(.75)-history.quantile(.25))
        rows.append((median,mad,iqr,len(history)))
    return pd.DataFrame(rows,columns=["baseline","mad","iqr","history_periods"],index=series.index)
