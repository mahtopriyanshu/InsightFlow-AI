"""Cached validated revenue and order forecast orchestration."""
import numpy as np
import pandas as pd
import streamlit as st

from streamlit_app.forecasting.backtesting import walk_forward
from streamlit_app.forecasting.data import completed_history
from streamlit_app.forecasting.models import ForecastPoint, ForecastReport, TargetForecast, predict_candidate
from streamlit_app.insights.comparisons import scope_label
from streamlit_app.utils.filters import FilterState

MIN_PERIODS = 12
INITIAL_TRAIN = 9
FORECAST_HORIZON = 3
MIN_MEDIAN_ORDERS = 25


def history_guardrail(data: pd.DataFrame) -> str | None:
    if len(data) < MIN_PERIODS:
        return f"Forecast unavailable: at least {MIN_PERIODS} complete monthly periods are required; {len(data)} are available."
    if float(pd.to_numeric(data["orders"], errors="coerce").fillna(0).median()) < MIN_MEDIAN_ORDERS:
        return f"Forecast unavailable: median monthly order volume is below the {MIN_MEDIAN_ORDERS}-order reliability guardrail."
    return None


def _target(data: pd.DataFrame, target: str, unit: str) -> TargetForecast:
    scores, predictions = walk_forward(data[target], INITIAL_TRAIN, data["month"])
    if not scores:
        raise ValueError(f"No eligible model for {target}")
    best = scores[0]
    future_values = np.maximum(0, predict_candidate(best.model, data[target], FORECAST_HORIZON, data["month"]))
    residuals = predictions.loc[predictions.model.eq(best.model), "residual"].abs()
    radius = float(residuals.quantile(.90)) if len(residuals) >= 5 else None
    future_months = pd.date_range(data.month.max() + pd.offsets.MonthBegin(1), periods=FORECAST_HORIZON, freq="MS")
    future = [ForecastPoint(month, float(value), max(0.0, float(value) - radius) if radius is not None else None, float(value) + radius if radius is not None else None) for month, value in zip(future_months, future_values)]
    selected = predictions.loc[predictions.model.eq(best.model)].copy()
    selected["month"] = data.iloc[selected.origin.astype(int)].month.to_numpy()
    return TargetForecast(target, unit, best.model, scores, data[["month", target]].copy(), selected, future, f"{best.model} achieved the lowest walk-forward WAPE ({best.wape:.2f}%) for {target}.")


@st.cache_data(ttl=300, show_spinner=False)
def build_forecast(filters: FilterState) -> ForecastReport:
    data = completed_history(filters)
    scope = scope_label(filters)
    periods = len(data.dropna(subset=["revenue", "orders"])) if not data.empty else 0
    earliest = data.month.min() if not data.empty else None
    latest = data.month.max() if not data.empty else None
    clean = data.dropna(subset=["revenue", "orders"]).reset_index(drop=True)
    reason = history_guardrail(clean)
    if reason:
        return ForecastReport(None, None, periods, earliest, latest, FORECAST_HORIZON, scope, reason)
    return ForecastReport(_target(clean, "revenue", "currency"), _target(clean, "orders", "count"), periods, earliest, latest, FORECAST_HORIZON, scope)
