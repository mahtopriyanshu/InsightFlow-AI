"""Sales Analytics page."""
import streamlit as st
from streamlit_app.anomalies import build_alerts
from streamlit_app.components.layout import render_alerts
from streamlit_app.components.compare_workspace import render_compare_workspace
from streamlit_app.components.forecast_workspace import render_forecast_workspace

from streamlit_app.charts.factory import (
    bar_chart,
    distribution_chart,
    performance_trends,
    trend_chart,
)
from streamlit_app.components.layout import dataframe_panel, kpi_card, page_header, ranking_list, render_insights, section_header, filter_context
from streamlit_app.insights import sales_insights
from streamlit_app.services.overview import (
    get_category_performance,
    get_monthly_performance,
    get_order_details,
    get_payment_methods,
    get_state_performance,
    get_sales_summary,
)
from streamlit_app.utils.filters import FilterState
from streamlit_app.utils.formatting import currency, number, percentage


def render(filters: FilterState) -> None:
    """Render revenue, order, category, payment, and geography analysis."""
    page_header(
        "Sales Analytics",
        "Explore revenue momentum, order economics, category mix, and markets.",
        "Commercial Performance",
    )
    filter_context(filters.start_date, filters.end_date, filters.states, filters.categories)
    with st.spinner("Analyzing commercial performance..."):
        monthly = get_monthly_performance(filters)
        categories = get_category_performance(filters, 20)
        payments = get_payment_methods(filters)
        states = get_state_performance(filters)
        details = get_order_details(filters)
        summary = get_sales_summary(filters)

    if monthly.empty:
        st.info("No sales data matches the current filters.")
        return

    row = summary.iloc[0]
    cards = st.columns(6)
    sales_kpis = [
        ("Total Revenue", currency(row["total_revenue"]), "R$"),
        ("Total Orders", number(row["total_orders"]), "▥"),
        ("Average Order Value", currency(row["average_order_value"]), "◫"),
        ("Items Sold", number(row["items_sold"]), "▣"),
        ("Revenue per Order", currency(row["total_revenue"] / max(row["total_orders"], 1)), "↗"),
        ("Cancellation Rate", percentage(row["cancellation_rate"]), "!"),
    ]
    for column, (label, value, icon) in zip(cards, sales_kpis):
        with column:
            kpi_card(label, value, icon)

    section_header("Sales performance", "Revenue, orders, payment mix, categories, and markets.")
    top = st.columns([1.65, 1])
    with top[0]:
        st.plotly_chart(performance_trends(monthly), use_container_width=True)
    with top[1]:
        st.plotly_chart(distribution_chart(payments, "payment_type", "payment_value", "Revenue by payment method"), use_container_width=True)
    section_header("Market and category mix", "Rank commercial contribution across products and customer regions.")
    columns = st.columns(2)
    with columns[0]:
        st.plotly_chart(
            bar_chart(
                categories.head(12).sort_values("revenue"),
                "category",
                "revenue",
                "Category revenue",
                horizontal=True,
            ),
            use_container_width=True,
        )
    with columns[1]:
        st.plotly_chart(
            bar_chart(
                states.head(12).sort_values("revenue"),
                "state",
                "revenue",
                "State-level revenue",
                horizontal=True,
            ),
            use_container_width=True,
        )

    trend_columns = st.columns(3)
    with trend_columns[0]:
        st.plotly_chart(trend_chart(monthly, "month", "revenue", "Revenue trend"), use_container_width=True)
    with trend_columns[1]:
        st.plotly_chart(trend_chart(monthly, "month", "orders", "Orders trend"), use_container_width=True)
    with trend_columns[2]:
        st.plotly_chart(trend_chart(monthly, "month", "average_order_value", "AOV trend"), use_container_width=True)
    columns = st.columns([1, 1])
    with columns[0]:
        st.markdown("#### Top performing categories")
        ranking_list(categories, "category", "revenue", currency, 8)
    with columns[1]:
        st.markdown("#### Top performing states")
        ranking_list(states, "state", "revenue", currency, 8)

    section_header("Sales insights", "Filter-aware movements, leaders, and concentration signals.")
    render_insights(sales_insights(filters, summary, monthly, categories, states, payments), columns=3)
    sales_alerts=[a for a in build_alerts(filters) if a.metric in {"revenue","orders","average_order_value"}]
    section_header("Sales anomalies & opportunities", "Completed-month movements outside recent robust commercial variation.")
    render_alerts(sales_alerts,columns=3)
    render_compare_workspace(filters)
    render_forecast_workspace(filters)

    st.markdown("### Order detail")
    st.caption("Most recent 1,000 matching orders; use browser table tools to sort.")
    dataframe_panel(details, height=470)
