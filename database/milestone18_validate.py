"""Live PostgreSQL M18 model, scope, guardrail, and performance validation."""
from datetime import date
from pathlib import Path
from time import perf_counter
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.forecasting import build_forecast
from streamlit_app.forecasting.models import CANDIDATES
from streamlit_app.services.common import get_filter_options
from streamlit_app.utils.filters import FilterState


def target_summary(target):
    assert target is not None
    assert {score.model for score in target.scores} == set(CANDIDATES)
    assert sum(score.selected for score in target.scores) == 1
    assert target.scores[0].selected and target.selected_model == target.scores[0].model
    assert len(target.future) == 3 and all(point.value >= 0 for point in target.future)
    assert all(math.isfinite(score.mae) and math.isfinite(score.rmse) for score in target.scores)
    assert all(score.wape is None or math.isfinite(score.wape) for score in target.scores)
    return {
        "selected": target.selected_model,
        "models": {score.model: {"MAE": round(score.mae, 2), "RMSE": round(score.rmse, 2), "WAPE": None if score.wape is None else round(score.wape, 2)} for score in target.scores},
        "future": [round(point.value, 2) for point in target.future],
        "intervals": [[round(point.lower, 2), round(point.upper, 2)] if point.lower is not None else None for point in target.future],
    }


def check(name, filters):
    started = perf_counter(); report = build_forecast(filters); elapsed = perf_counter() - started
    assert report.scope
    if report.unavailable_reason:
        assert report.revenue is None and report.orders is None
        result = {"periods": report.complete_periods, "unavailable": report.unavailable_reason, "seconds": round(elapsed, 3)}
    else:
        assert report.complete_periods >= 12
        result = {"periods": report.complete_periods, "range": [str(report.earliest_period.date()), str(report.latest_period.date())], "revenue": target_summary(report.revenue), "orders": target_summary(report.orders), "seconds": round(elapsed, 3)}
    print(name, result)
    return report, elapsed


def main():
    lo, hi, _, categories = get_filter_options()
    category = "health_beauty" if "health_beauty" in categories else categories[0]
    period = (date(2018, 1, 1), date(2018, 6, 30))
    contexts = {
        "full": FilterState(lo, hi),
        "date": FilterState(*period),
        "SP": FilterState(lo, hi, ("SP",)),
        "category": FilterState(lo, hi, (), (category,)),
        "date_SP": FilterState(*period, ("SP",)),
        "date_category": FilterState(*period, (), (category,)),
        "date_SP_category": FilterState(*period, ("SP",), (category,)),
        "partial_trailing_month": FilterState(lo, date(2018, 9, 15)),
    }
    reports = {}
    for name, filters in contexts.items():
        reports[name], _ = check(name, filters)
    assert reports["partial_trailing_month"].latest_period.month == 8
    started = perf_counter(); build_forecast(contexts["full"]); cached = perf_counter() - started
    print("cached_full_seconds", round(cached, 4))


if __name__ == "__main__":
    main()
