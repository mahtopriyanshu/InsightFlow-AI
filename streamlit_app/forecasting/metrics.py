"""Forecast error metrics with safe zero handling."""
import numpy as np


def mae(actual, predicted) -> float:
    return float(np.mean(np.abs(np.asarray(actual, dtype=float) - np.asarray(predicted, dtype=float))))


def rmse(actual, predicted) -> float:
    return float(np.sqrt(np.mean((np.asarray(actual, dtype=float) - np.asarray(predicted, dtype=float)) ** 2)))


def wape(actual, predicted) -> float | None:
    denominator = float(np.abs(np.asarray(actual, dtype=float)).sum())
    return None if denominator == 0 else 100.0 * float(np.abs(np.asarray(actual, dtype=float) - np.asarray(predicted, dtype=float)).sum()) / denominator
