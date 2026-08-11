"""Live correctness, filter-scope, reconciliation, and performance checks for M12."""
from datetime import date
from pathlib import Path
from time import perf_counter
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit_app.insights import customer_insights
from streamlit_app.services.common import get_filter_options
from streamlit_app.services.customers import get_customer_locations, get_customer_metrics, get_top_customers
from streamlit_app.services.rfm import (
    get_pareto_analysis, get_rfm_customers, get_segment_geography, get_segment_summary,
)
from streamlit_app.utils.filters import FilterState


def validate(name: str, filters: FilterState) -> None:
    start = perf_counter()
    profiles = get_rfm_customers(filters)
    query_and_scoring = perf_counter() - start
    start = perf_counter()
    summary = get_segment_summary(profiles)
    _, pareto = get_pareto_analysis(profiles)
    geography = get_segment_geography(profiles)
    aggregation = perf_counter() - start
    metrics = get_customer_metrics(filters)
    locations = get_customer_locations(filters)
    top = get_top_customers(filters)
    insights = customer_insights(filters, metrics, locations, top, summary, pareto, geography)

    assert profiles["customer_unique_id"].is_unique
    assert profiles["segment"].notna().all()
    assert profiles[["r_score", "f_score", "m_score"]].isin(range(1, 6)).all().all()
    assert int(summary["customers"].sum()) == len(profiles)
    assert abs(float(summary["revenue"].sum()) - float(profiles["monetary"].sum())) < .01
    assert int(metrics.iloc[0]["unique_customers"]) == len(profiles)
    assert abs(float(metrics.iloc[0]["revenue_per_customer"]) * len(profiles)
               - float(profiles["monetary"].sum())) < .05
    assert all(insight.evidence is not None for insight in insights)
    if filters.states:
        assert set(profiles["state"].dropna()).issubset(set(filters.states))
        assert all("SP" in insight.scope for insight in insights)
    if filters.categories:
        assert all(filters.categories[0] in insight.scope for insight in insights)
    print(name, {
        "customers": len(profiles), "revenue": round(float(profiles["monetary"].sum()), 2),
        "segments": summary.set_index(summary["segment"].astype(str))["customers"].to_dict(),
        "pareto_80": round(pareto["customers_for_80pct_revenue"], 2),
        "rfm_query_score_s": round(query_and_scoring, 3),
        "aggregate_s": round(aggregation, 3), "insights": len(insights),
    })


def main() -> None:
    min_date, max_date, _, categories = get_filter_options()
    category = "health_beauty" if "health_beauty" in categories else categories[0]
    period = (date(2018, 1, 1), date(2018, 6, 30))
    contexts = {
        "full": FilterState(min_date, max_date),
        "date": FilterState(*period),
        "SP": FilterState(min_date, max_date, ("SP",)),
        "category": FilterState(min_date, max_date, (), (category,)),
        "date_SP": FilterState(*period, ("SP",)),
        "date_category": FilterState(*period, (), (category,)),
        "date_SP_category": FilterState(*period, ("SP",), (category,)),
    }
    for name, filters in contexts.items():
        validate(name, filters)


if __name__ == "__main__":
    main()
