"""Chronological expanding-window forecasting validation."""
import pandas as pd
from streamlit_app.forecasting.metrics import mae, rmse, wape
from streamlit_app.forecasting.models import CANDIDATES, ModelScore, predict_candidate


def walk_forward(series: pd.Series, initial_train: int = 9, months=None) -> tuple[list[ModelScore], pd.DataFrame]:
    values = pd.to_numeric(series, errors="coerce").dropna().reset_index(drop=True)
    if len(values) <= initial_train:
        return [], pd.DataFrame()
    rows = []
    for origin in range(initial_train, len(values)):
        train = values.iloc[:origin]
        train_months = pd.Series(months).iloc[:origin] if months is not None else None
        actual = float(values.iloc[origin])
        for name in CANDIDATES:
            try:
                predicted = max(0.0, float(predict_candidate(name, train, 1, train_months)[0]))
                rows.append({"origin": origin, "model": name, "actual": actual, "predicted": predicted, "residual": actual - predicted})
            except (ValueError, ArithmeticError, OverflowError):
                continue
    predictions = pd.DataFrame(rows)
    scores = []
    for name, group in predictions.groupby("model", sort=False):
        scores.append(ModelScore(name, mae(group.actual, group.predicted), rmse(group.actual, group.predicted), wape(group.actual, group.predicted), len(group)))
    scores.sort(key=lambda x: (float("inf") if x.wape is None else x.wape, x.mae, x.rmse))
    if scores:
        scores = [ModelScore(s.model, s.mae, s.rmse, s.wape, s.observations, i == 0) for i, s in enumerate(scores)]
    return scores, predictions
