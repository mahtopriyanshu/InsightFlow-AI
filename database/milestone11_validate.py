"""Live filter-awareness and evidence validation for Milestone 11."""
from datetime import date
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit_app.insights import (
    customer_insights, delivery_insights, executive_insights,
    product_insights, review_insights, sales_insights, seller_insights,
)
from streamlit_app.services import commerce, customers, operations, overview
from streamlit_app.services.common import get_filter_options
from streamlit_app.utils.filters import FilterState


def build(filters: FilterState) -> dict[str, list]:
    kpis = overview.get_kpis(filters)
    monthly = overview.get_monthly_performance(filters)
    categories = overview.get_category_performance(filters, 100)
    states = overview.get_state_performance(filters)
    payments = overview.get_payment_methods(filters)
    summary = overview.get_sales_summary(filters)
    customer_metrics = customers.get_customer_metrics(filters)
    locations = customers.get_customer_locations(filters)
    top_customers = customers.get_top_customers(filters)
    products = commerce.get_product_performance(filters, 100)
    sellers = commerce.get_seller_performance(filters)
    delivery_metrics = operations.get_delivery_metrics(filters)
    delivery_states = operations.get_delivery_by_state(filters)
    review_metrics = operations.get_review_metrics(filters)
    review_distribution = operations.get_review_distribution(filters)
    review_categories = operations.get_review_by_category(filters, 100)
    relationship = operations.get_delivery_review_relationship(filters)
    customer_mix = overview.get_customer_mix(filters)
    return {
        "executive": executive_insights(filters, kpis, categories, states, payments, customer_mix),
        "sales": sales_insights(filters, summary, monthly, categories, states, payments),
        "customers": customer_insights(filters, customer_metrics, locations, top_customers),
        "products": product_insights(filters, products, review_categories),
        "sellers": seller_insights(filters, sellers),
        "delivery": delivery_insights(filters, delivery_metrics, delivery_states),
        "reviews": review_insights(filters, review_metrics, review_distribution, review_categories, relationship),
    }


def main() -> None:
    min_date, max_date, _, categories = get_filter_options()
    category = "health_beauty" if "health_beauty" in categories else categories[0]
    contexts = {
        "full": FilterState(min_date, max_date),
        "date": FilterState(date(2018, 1, 1), date(2018, 6, 30)),
        "state": FilterState(min_date, max_date, ("SP",)),
        "category": FilterState(min_date, max_date, (), (category,)),
        "combined": FilterState(date(2018, 1, 1), date(2018, 6, 30), ("SP",), (category,)),
    }
    for context, filters in contexts.items():
        results = build(filters)
        for domain, insights in results.items():
            assert len(insights) <= (6 if domain == "executive" else 5)
            assert all(insight.evidence is not None for insight in insights)
            assert all(insight.scope for insight in insights)
            if filters.states:
                assert all("SP" in insight.scope for insight in insights)
            if filters.categories:
                assert all(category in insight.scope for insight in insights)
        print(context, {domain: len(items) for domain, items in results.items()})


if __name__ == "__main__":
    main()
