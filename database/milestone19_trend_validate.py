"""Live PostgreSQL reconciliation for governed monthly Assistant trends."""
from pathlib import Path
import math
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.assistant import ask_assistant
from streamlit_app.services.common import get_filter_options
from streamlit_app.services.operations import get_delivery_trend, get_review_trend
from streamlit_app.services.overview import get_monthly_performance
from streamlit_app.utils.filters import FilterState


QUESTIONS = {
    "payment_revenue": "Show the monthly revenue trend.",
    "orders": "Show the monthly order trend.",
    "average_order_value": "Show how average order value changed month by month.",
    "unique_customers": "Show the monthly trend of unique customers.",
    "delivery_rate": "Show the monthly delivery rate trend.",
    "late_delivery_rate": "Show how late-delivery rate changed month by month.",
    "average_delivery_days": "Show the monthly average delivery days trend.",
    "average_review_score": "Show the monthly average review score trend.",
    "negative_review_rate": "Show the monthly negative-review rate trend.",
}


def _close_series(left, right):
    merged = left.merge(right, on="month", suffixes=("_assistant", "_service"))
    assert len(merged) == len(left) == len(right)
    for row in merged.itertuples(index=False):
        pair = row[1:]
        if all(pd.isna(value) for value in pair):
            continue
        assert all(pd.notna(value) for value in pair)
        assert math.isclose(float(pair[0]), float(pair[1]), rel_tol=1e-9, abs_tol=1e-9)


def main():
    start, end, _, categories = get_filter_options()
    filters = FilterState(start, end)
    answers = {metric: ask_assistant(question, filters, use_llm=False) for metric, question in QUESTIONS.items()}
    for metric, answer in answers.items():
        assert len(answer.data) > 1 and answer.data.month.is_monotonic_increasing
        assert answer.metadata.metric == metric and answer.metadata.chart_type == "line"

    commercial = get_monthly_performance(filters).rename(columns={"revenue": "payment_revenue"})
    for metric in ("payment_revenue", "orders", "average_order_value"):
        _close_series(answers[metric].data[["month", metric]], commercial[["month", metric]])
    delivery = get_delivery_trend(filters).rename(columns={"late_rate": "late_delivery_rate"})
    for metric in ("late_delivery_rate", "average_delivery_days"):
        _close_series(answers[metric].data[["month", metric]], delivery[["month", metric]])
    reviews = get_review_trend(filters)
    _close_series(answers["average_review_score"].data[["month", "average_review_score"]], reviews[["month", "average_review_score"]])

    category = "health_beauty" if "health_beauty" in categories else categories[0]
    scoped = FilterState(start, end, ("SP",), (category,))
    for metric, question in QUESTIONS.items():
        answer = ask_assistant(question, scoped, use_llm=False)
        assert answer.metadata.metric == metric
        assert "state: SP" in answer.scope and f"category: {category}" in answer.scope
        assert answer.data.month.is_monotonic_increasing
    print({"metrics": len(answers), "canonical_reconciliations": 6, "combined_filter_metrics": len(QUESTIONS), "status": "passed"})


if __name__ == "__main__":
    main()
