"""Executive Overview page."""
import streamlit as st
from streamlit_app.anomalies import build_alerts
from streamlit_app.components.layout import render_alerts
from streamlit_app.components.health_center import render_health_center
from streamlit_app.health import build_health_report

from streamlit_app.charts.factory import (
    bar_chart,
    distribution_chart,
    performance_trends,
)
from streamlit_app.components.layout import (
    empty_state,
    kpi_card,
    page_header,
    filter_context,
    health_indicator,
    section_header,
    render_insights,
)
from streamlit_app.insights import executive_insights
from streamlit_app.services.overview import (
    get_category_performance,
    get_kpis,
    get_monthly_performance,
    get_state_performance,
    get_payment_methods,
    get_customer_mix,
    get_delivery_outcomes,
)
from streamlit_app.utils.filters import FilterState
from streamlit_app.utils.formatting import currency, number, percentage


def render(filters: FilterState) -> None:
    """Render executive KPIs, trends, and deterministic insights."""
    page_header(
        "Executive Overview",
        "Real-time intelligence across revenue, customers, products and fulfillment.",
        "Command Center",
    )
    filter_context(filters.start_date, filters.end_date, filters.states, filters.categories)
    with st.spinner("Building your executive view..."):
        kpis = get_kpis(filters)
        monthly = get_monthly_performance(filters)
        categories = get_category_performance(filters, 10)
        states = get_state_performance(filters)
        payments = get_payment_methods(filters)
        customer_mix = get_customer_mix(filters)
        delivery_outcomes = get_delivery_outcomes(filters)

    if kpis.empty or int(kpis.iloc[0]["total_orders"] or 0) == 0:
        empty_state("No orders match the selected filters.")
        return

    row = kpis.iloc[0]
    cards = st.columns(6)
    values = [
        ("Total Revenue", currency(row["total_revenue"]), "R$"),
        ("Total Orders", number(row["total_orders"]), "▤"),
        ("Unique Customers", number(row["unique_customers"]), "♙"),
        ("Average Order Value", currency(row["average_order_value"]), "◫"),
        ("Average Review", number(row["average_review_score"], 2), "★"),
        ("Delivery Rate", percentage(row["delivery_rate"]), "✓"),
    ]
    for column, (label, value, icon) in zip(cards, values):
        with column:
            kpi_card(label, value, icon)

    with st.spinner("Scoring transparent business health..."):
        health_report=build_health_report(filters)
    render_health_center(health_report)

    section_header("Performance dashboard", "Commercial momentum, fulfillment outcomes, and customer composition.")
    chart_columns = st.columns([1.45, 1, 1])
    with chart_columns[0]:
        st.plotly_chart(performance_trends(monthly), use_container_width=True)
    with chart_columns[1]:
        st.plotly_chart(
            distribution_chart(
                delivery_outcomes,
                "delivery_outcome",
                "orders",
                "Delivery performance",
            ),
            use_container_width=True,
        )
    with chart_columns[2]:
        st.plotly_chart(
            distribution_chart(
                customer_mix,
                "customer_type",
                "customers",
                "Customer mix",
            ),
            use_container_width=True,
        )

    chart_columns = st.columns([1.2, 1, 1.2])
    with chart_columns[0]:
        st.plotly_chart(bar_chart(states.head(8).sort_values("revenue"), "state", "revenue", "Top states by revenue", horizontal=True), use_container_width=True)
    with chart_columns[1]:
        st.plotly_chart(distribution_chart(payments, "payment_type", "payment_value", "Payment method distribution"), use_container_width=True)
    with chart_columns[2]:
        st.plotly_chart(bar_chart(categories.head(8).sort_values("revenue"), "category", "revenue", "Top categories", horizontal=True), use_container_width=True)

    section_header("Dynamic business insights", "Prioritized deterministic observations with traceable evidence.")
    render_insights(executive_insights(filters, kpis, categories, states, payments, customer_mix), columns=3)
    section_header("Alerts & opportunities", "Unusual completed-month behavior relative to trailing robust historical baselines.")
    render_alerts(build_alerts(filters),columns=3)
