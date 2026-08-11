"""Measured customer service and RFM timings plus final segment evidence."""
from pathlib import Path
from time import perf_counter
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit_app.database.connection import query_dataframe
from streamlit_app.services.common import get_filter_options
from streamlit_app.services.customers import get_customer_locations, get_customer_metrics, get_top_customers
from streamlit_app.services.rfm import get_pareto_analysis, get_rfm_customers, get_segment_summary
from streamlit_app.utils.filters import FilterState


def main() -> None:
    start_date, end_date, _, _ = get_filter_options()
    filters = FilterState(start_date, end_date)
    query_dataframe.clear()
    started = perf_counter()
    get_customer_metrics(filters)
    get_customer_locations(filters)
    get_top_customers(filters)
    legacy_services = perf_counter() - started

    get_rfm_customers.clear()
    started = perf_counter()
    profiles = get_rfm_customers(filters)
    rfm_query_scoring = perf_counter() - started
    started = perf_counter()
    summary = get_segment_summary(profiles)
    _, pareto = get_pareto_analysis(profiles)
    aggregation = perf_counter() - started
    print("timings", {
        "existing_customer_service_bundle_s": round(legacy_services, 3),
        "rfm_query_and_scoring_s": round(rfm_query_scoring, 3),
        "segment_and_pareto_s": round(aggregation, 3),
    })
    print("segments")
    print(summary[["segment", "customers", "customer_share", "revenue", "revenue_share"]].to_string(index=False))
    print("pareto", pareto)


if __name__ == "__main__":
    main()
