"""Focused deterministic M18 forecasting tests (no live database required)."""
from contextlib import nullcontext
import math
import numpy as np
import pandas as pd

from streamlit_app.forecasting.backtesting import walk_forward
from streamlit_app.forecasting.data import construct_completed_history
from streamlit_app.forecasting.engine import FORECAST_HORIZON, history_guardrail
from streamlit_app.forecasting.features import lag_features
from streamlit_app.forecasting.metrics import mae, rmse, wape
from streamlit_app.forecasting.models import predict_candidate
from streamlit_app.components import forecast_workspace


def _coverage():
    return pd.DataFrame({
        "month": pd.to_datetime(["2017-01-01", "2017-02-01", "2017-03-01", "2017-04-01"]),
        "first_day": pd.to_datetime(["2017-01-05", "2017-02-01", "2017-03-01", "2017-04-01"]),
        "last_day": pd.to_datetime(["2017-01-31", "2017-02-28", "2017-03-31", "2017-04-20"]),
    })


def test_complete_month_construction_excludes_partial_boundaries():
    scoped = pd.DataFrame({"month": pd.to_datetime(["2017-01-01", "2017-02-01", "2017-03-01", "2017-04-01"]), "revenue": [1, 2, 3, 4], "orders": [1, 2, 3, 4]})
    result = construct_completed_history(scoped, _coverage())
    assert result.month.dt.strftime("%Y-%m").tolist() == ["2017-02", "2017-03"]


def test_missing_scoped_period_is_preserved_as_zero():
    scoped = pd.DataFrame({"month": pd.to_datetime(["2017-02-01"]), "revenue": [20], "orders": [2]})
    result = construct_completed_history(scoped, _coverage())
    assert result.orders.tolist() == [2, 0] and result.revenue.tolist() == [20, 0]


def test_lags_and_rolling_features_use_only_prior_values():
    series = pd.Series([1.0, 2.0, 3.0, 99.0], index=pd.date_range("2018-01-01", periods=4, freq="MS"))
    frame = lag_features(series)
    assert frame.iloc[3]["lag_1"] == 3 and frame.iloc[3]["rolling_mean_3"] == 2
    assert frame.iloc[3]["month"] == 4 and frame.iloc[3]["quarter"] == 2


def test_walk_forward_is_expanding_and_chronological():
    series = pd.Series(np.arange(1, 14, dtype=float))
    _, predictions = walk_forward(series, initial_train=7)
    assert sorted(predictions.origin.unique().tolist()) == list(range(7, 13))
    assert predictions.groupby("model").size().nunique() == 1


def test_error_metrics():
    actual, predicted = [10, 20], [8, 24]
    assert mae(actual, predicted) == 3
    assert math.isclose(rmse(actual, predicted), math.sqrt(10))
    assert wape(actual, predicted) == 20


def test_wape_zero_denominator_is_unavailable():
    assert wape([0, 0], [0, 1]) is None


def test_model_ranking_is_objective_and_unique():
    scores, _ = walk_forward(pd.Series(np.arange(10, 30, dtype=float)), initial_train=9)
    assert len(scores) == 5 and sum(score.selected for score in scores) == 1
    keys = [(float("inf") if score.wape is None else score.wape, score.mae, score.rmse) for score in scores]
    assert keys == sorted(keys)


def test_insufficient_history_guardrail():
    data = pd.DataFrame({"orders": [100] * 11})
    assert "at least 12" in history_guardrail(data)


def test_tiny_filtered_scope_guardrail():
    data = pd.DataFrame({"orders": [3] * 12})
    assert "25-order" in history_guardrail(data)


def test_valid_history_passes_guardrail():
    assert history_guardrail(pd.DataFrame({"orders": [100] * 12})) is None


def test_forecast_horizon_and_nonnegative_output():
    forecast = predict_candidate("Naive", pd.Series([10.0] * 12), FORECAST_HORIZON)
    assert len(forecast) == 3 and np.all(forecast >= 0)


def test_empty_filtered_scope_is_safe():
    result = construct_completed_history(pd.DataFrame(), _coverage())
    assert len(result) == 2 and result[["orders", "revenue"]].to_numpy().sum() == 0


def test_forecast_service_failure_isolated_to_workspace(monkeypatch):
    warnings = []
    monkeypatch.setattr(forecast_workspace, "section_header", lambda *args: None)
    monkeypatch.setattr(forecast_workspace.st, "toggle", lambda *args, **kwargs: True)
    monkeypatch.setattr(forecast_workspace.st, "spinner", lambda *args, **kwargs: nullcontext())
    monkeypatch.setattr(forecast_workspace.st, "warning", warnings.append)
    monkeypatch.setattr(forecast_workspace, "build_forecast", lambda filters: (_ for _ in ()).throw(RuntimeError("sensitive detail")))

    forecast_workspace.render_forecast_workspace(object())

    assert warnings == ["Forecasting is temporarily unavailable. The rest of Sales Analytics remains available."]
