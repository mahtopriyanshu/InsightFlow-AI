"""Validated completed-month forecasting data preparation."""
import pandas as pd
from streamlit_app.anomalies.baselines import complete_months
from streamlit_app.services.anomaly_history import get_business_history
from streamlit_app.services.common import get_filter_options
from streamlit_app.utils.filters import FilterState


def construct_completed_history(scoped: pd.DataFrame, coverage: pd.DataFrame) -> pd.DataFrame:
    """Align scoped observations to months proven complete by global coverage.

    A filtered category/state need not trade on the first and last calendar day;
    completeness must therefore be established from the unfiltered dataset, not
    from sparse scoped activity. Missing scoped months are genuine zero-volume
    periods and remain in the chronological series.
    """
    eligible = complete_months(coverage)
    if eligible.empty:
        return pd.DataFrame(columns=["month", "revenue", "orders"])
    calendar = pd.DatetimeIndex(pd.to_datetime(eligible["month"]).drop_duplicates().sort_values())
    data = scoped.copy()
    if data.empty:
        data = pd.DataFrame(index=calendar)
    else:
        data["month"] = pd.to_datetime(data["month"])
        data = data.set_index("month").reindex(calendar)
    for column in ("revenue", "orders"):
        values = data[column] if column in data else pd.Series(0.0, index=data.index)
        data[column] = pd.to_numeric(values, errors="coerce").fillna(0.0)
    return data.rename_axis("month").reset_index()


def completed_history(filters: FilterState) -> pd.DataFrame:
    scoped = get_business_history(filters)
    dataset_start, _, _, _ = get_filter_options()
    coverage = get_business_history(FilterState(dataset_start, filters.end_date))
    return construct_completed_history(scoped, coverage)
