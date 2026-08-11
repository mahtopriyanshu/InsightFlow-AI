"""Typed forecasting contracts and candidate model adapters."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.holtwinters import ExponentialSmoothing


@dataclass(frozen=True)
class ModelScore:
    model: str
    mae: float
    rmse: float
    wape: float | None
    observations: int
    selected: bool = False


@dataclass(frozen=True)
class ForecastPoint:
    period: pd.Timestamp
    value: float
    lower: float | None = None
    upper: float | None = None


@dataclass
class TargetForecast:
    target: str
    unit: str
    selected_model: str
    scores: list[ModelScore]
    history: pd.DataFrame
    backtest: pd.DataFrame
    future: list[ForecastPoint]
    rationale: str


@dataclass
class ForecastReport:
    revenue: TargetForecast | None
    orders: TargetForecast | None
    complete_periods: int
    earliest_period: pd.Timestamp | None
    latest_period: pd.Timestamp | None
    horizon: int
    scope: str
    unavailable_reason: str | None = None


def _rf_features(values: list[float], index: int, month: int) -> list[float]:
    lag1, lag2, lag3 = values[-1], values[-2], values[-3]
    prior = np.asarray(values[-3:], dtype=float)
    return [lag1, lag2, lag3, float(prior.mean()), float(prior.std(ddof=0)), month, ((month - 1) // 3) + 1, index]


def predict_candidate(name: str, train: pd.Series, steps: int = 1, months=None) -> np.ndarray:
    """Fit one candidate and recursively forecast without future leakage."""
    values = [float(v) for v in train]
    if name == "Naive":
        return np.repeat(values[-1], steps)
    if name == "Drift":
        slope = (values[-1] - values[0]) / max(len(values) - 1, 1)
        return np.asarray([values[-1] + slope * i for i in range(1, steps + 1)])
    if name == "Linear Trend":
        x = np.arange(len(values)).reshape(-1, 1)
        model = LinearRegression().fit(x, values)
        return model.predict(np.arange(len(values), len(values) + steps).reshape(-1, 1))
    if name == "Holt":
        fitted = ExponentialSmoothing(values, trend="add", seasonal=None, initialization_method="estimated").fit(optimized=True)
        return np.asarray(fitted.forecast(steps), dtype=float)
    if name == "Random Forest":
        if len(values) < 7:
            raise ValueError("Random Forest requires at least seven periods")
        x, y = [], []
        month_values = list(pd.DatetimeIndex(pd.to_datetime(list(months))).month) if months is not None else [((i % 12) + 1) for i in range(len(values))]
        for i in range(3, len(values)):
            x.append(_rf_features(values[:i], i, month_values[i]))
            y.append(values[i])
        model = RandomForestRegressor(n_estimators=200, min_samples_leaf=2, random_state=42, n_jobs=1).fit(x, y)
        generated = values[:]
        output = []
        last_month = month_values[-1]
        for step in range(steps):
            future_month = ((last_month + step) % 12) + 1
            value = float(model.predict([_rf_features(generated, len(generated), future_month)])[0])
            output.append(value); generated.append(value)
        return np.asarray(output)
    raise ValueError(f"Unsupported model: {name}")


CANDIDATES = ("Naive", "Drift", "Linear Trend", "Holt", "Random Forest")
