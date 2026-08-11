"""Delivery Analytics page."""
import streamlit as st
from streamlit_app.anomalies import build_alerts
from streamlit_app.components.layout import render_alerts

from streamlit_app.charts.factory import (
    bar_chart,
    distribution_chart,
    histogram_chart,
    status_donut,
)
from streamlit_app.components.layout import (
    dataframe_panel,
    kpi_card,
    page_header,
)
from streamlit_app.insights import delivery_insights
from streamlit_app.services.operations import (
    get_delivery_by_state,
    get_delivery_distribution,
    get_delivery_metrics,
    get_delivery_trend,
)
from streamlit_app.utils.filters import FilterState
from streamlit_app.utils.formatting import currency, number, percentage
from streamlit_app.charts.factory import trend_chart
from streamlit_app.components.layout import health_indicator, section_header
from streamlit_app.components.layout import render_insights
from streamlit_app.components.layout import filter_context


def render(filters: FilterState) -> None:
    """Render delivery speed, delays, geography, and freight analysis."""
    page_header(
        "Delivery Analytics",
        "Monitor delivery speed, promised-date performance, and operational risk.",
        "Fulfilment Operations",
    )
    filter_context(filters.start_date, filters.end_date, filters.states, filters.categories)
    with st.spinner("Calculating fulfilment performance..."):
        metrics = get_delivery_metrics(filters)
        trend = get_delivery_trend(filters)
        by_state = get_delivery_by_state(filters)
        distribution = get_delivery_distribution(filters)

    if metrics.empty or distribution.empty:
        st.info("No completed delivery data matches the current filters.")
        return

    row = metrics.iloc[0]
    columns = st.columns(6)
    values = [
        ("Delivery Rate", percentage(row["delivery_rate"])),
        ("Average Delivery", f"{number(row['average_delivery_days'], 1)} days"),
        ("Late Delivery Rate", percentage(row["late_rate"])),
        ("Orders Delivered", number(row["delivered_orders"]),),
        ("Cancellation Rate", percentage(row["cancellation_rate"])),
        ("Average Freight", currency(row["average_freight"])),
    ]
    for column, (label, value) in zip(columns, values):
        with column:
            kpi_card(label, value)

    section_header("Fulfillment health", "Delivery completion and promise-date performance from eligible orders.")
    health_indicator("Fulfillment Health", 100 - float(row["late_rate"] or 0), percentage(100 - float(row["late_rate"] or 0)), "Share of delivered orders that were on time or early")

    chart_columns = st.columns(2)
    with chart_columns[0]:
        st.plotly_chart(
            histogram_chart(
                distribution,
                "actual_delivery_days",
                "Delivery-time distribution",
                35,
            ),
            use_container_width=True,
        )
    outcome = (
        distribution.groupby("delivery_performance", as_index=False)
        .size()
        .rename(columns={"size": "orders"})
    )
    with chart_columns[1]:
        st.plotly_chart(
            status_donut(
                outcome,
                "delivery_performance",
                "orders",
                "On-time versus late delivery",
                {"on_time_or_early": "#22C55E", "late": "#EF4444", "not_delivered": "#F59E0B"},
            ),
            use_container_width=True,
        )

    st.plotly_chart(trend_chart(trend, "month", "average_delivery_days", "Delivery performance trend", "Days"), use_container_width=True)

    state_columns = st.columns([1.15, 1])
    with state_columns[0]:
        st.plotly_chart(bar_chart(by_state.sort_values("late_rate").tail(15), "state", "late_rate", "Late-delivery ranking", horizontal=True), use_container_width=True)
    with state_columns[1]:
        st.plotly_chart(bar_chart(by_state.sort_values("average_delivery_days").tail(15), "state", "average_delivery_days", "Average delivery days by state", horizontal=True), use_container_width=True)

    section_header("Operational insights", "Comparable-period movements and state rankings with minimum delivery samples.")
    render_insights(delivery_insights(filters, metrics, by_state), columns=3)
    delivery_alerts=[a for a in build_alerts(filters) if a.metric in {"delivery_rate","late_rate","average_delivery_days"}]
    section_header("Delivery anomalies & opportunities", "Unusual completed-month fulfillment behavior with eligible-order guardrails.")
    render_alerts(delivery_alerts,columns=3)

    st.markdown("### State operating detail")
    dataframe_panel(by_state, height=420)
