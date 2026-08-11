"""Synthetic edge-case coverage for the robust M14 detector."""
from datetime import date
import numpy as np
import pandas as pd
from streamlit_app.anomalies.baselines import complete_months
from streamlit_app.anomalies.detectors import detect_series
from streamlit_app.utils.filters import FilterState

FILTERS=FilterState(date(2020,1,1),date(2021,12,31))
def frame(values,samples=None):
    return pd.DataFrame({"month":pd.date_range("2020-01-01",periods=len(values),freq="MS"),"revenue":values,"orders":samples or [100]*len(values)})
def detect(values,samples=None):return detect_series(frame(values,samples),"revenue",FILTERS,sample_column="orders",min_sample=50)

def test_stable_series_has_no_alert():assert not detect([100]*12)
def test_clear_positive_spike():assert detect([100]*8+[250])[-1].category=="opportunity"
def test_clear_negative_drop():assert detect([100]*8+[30])[-1].category=="anomaly"
def test_noisy_normal_series_is_not_flagged():assert not detect([100,105,95,103,97,106,94,102,98,104])
def test_insufficient_history():assert not detect([100,100,250])
def test_zero_baseline_is_safe():assert detect([0]*8+[100])
def test_missing_value_is_safe():assert not detect([100,100,np.nan,100,100,100,100,100])
def test_partial_period_is_excluded():
    data=pd.DataFrame({"month":pd.to_datetime(["2020-01-01","2020-02-01"]),"first_day":pd.to_datetime(["2020-01-01","2020-02-01"]),"last_day":pd.to_datetime(["2020-01-31","2020-02-15"])})
    assert len(complete_months(data))==1
def test_extreme_outlier_is_flagged():assert abs(detect([100,101,99,100,102,98,100,101,1000])[-1].deviation)>=3.5
def test_repeated_equal_values_are_safe():assert not detect([50]*20)
def test_tiny_sample_group_is_not_flagged():assert not detect([100]*8+[500],[100]*8+[3])
