"""Review Analytics page."""
import streamlit as st
from streamlit_app.anomalies import build_alerts
from streamlit_app.components.layout import render_alerts

from streamlit_app.charts.factory import bar_chart, trend_chart
from streamlit_app.components.layout import (
    dataframe_panel,
    kpi_card,
    page_header,
    health_indicator,
    section_header,
    filter_context,
    ranking_list,
    render_insights,
)
from streamlit_app.insights import review_insights
from streamlit_app.services.operations import (
    get_delivery_review_relationship,
    get_negative_reviews,
    get_review_by_category,
    get_review_distribution,
    get_review_metrics,
    get_review_trend,
)
from streamlit_app.utils.filters import FilterState
from streamlit_app.utils.formatting import number, percentage


def render(filters: FilterState) -> None:
    """Render review quality, trends, categories, and delivery relationships."""
    page_header(
        "Review Analytics",
        "Connect customer sentiment to product categories and delivery outcomes.",
        "Customer Experience",
    )
    filter_context(filters.start_date, filters.end_date, filters.states, filters.categories)
    with st.spinner("Analyzing customer reviews..."):
        metrics = get_review_metrics(filters)
        distribution = get_review_distribution(filters)
        trend = get_review_trend(filters)
        categories = get_review_by_category(filters, 100)
        relationship = get_delivery_review_relationship(filters)

    if metrics.empty or int(metrics.iloc[0]["total_reviews"] or 0) == 0:
        st.info("No reviews match the current filters.")
        return

    row = metrics.iloc[0]
    five_star = distribution.loc[distribution["review_score"].eq(5), "reviews"].sum()
    one_star = distribution.loc[distribution["review_score"].eq(1), "reviews"].sum()
    columns = st.columns(6)
    values = [
        ("Average Rating", number(row["average_review_score"], 2)),
        ("Total Reviews", number(row["total_reviews"])),
        ("Negative Reviews", number(row["negative_reviews"])),
        ("Negative Review Rate", percentage(row["negative_review_rate"])),
        ("5-Star Review Rate", percentage(100 * five_star / max(float(row["total_reviews"]), 1))),
        ("1-Star Review Rate", percentage(100 * one_star / max(float(row["total_reviews"]), 1))),
    ]
    for column, (label, value) in zip(columns, values):
        with column:
            kpi_card(label, value)

    section_header("Customer satisfaction", "A rating-based experience indicator grounded in submitted reviews.")
    health_indicator("Satisfaction Health", float(row["average_review_score"] or 0) * 20, f"{number(row['average_review_score'], 2)} / 5", "Average review score across matching orders")

    chart_columns = st.columns(2)
    with chart_columns[0]:
        st.plotly_chart(
            bar_chart(
                distribution,
                "review_score",
                "reviews",
                "Review score distribution",
            ),
            use_container_width=True,
        )
    with chart_columns[1]:
        st.plotly_chart(
            trend_chart(
                trend,
                "month",
                "average_review_score",
                "Average review score trend",
            ),
            use_container_width=True,
        )

    section_header("Category experience", "Best and lowest reviewed categories with at least 25 reviews.")
    category_columns = st.columns([1, 1, 1.15])
    with category_columns[0]:
        st.markdown("#### Best reviewed")
        ranking_list(categories.sort_values("average_review_score", ascending=False), "category", "average_review_score", lambda value: f"{number(value, 2)} ★", 7)
    with category_columns[1]:
        st.markdown("#### Lowest reviewed")
        ranking_list(categories.sort_values("average_review_score", ascending=True), "category", "average_review_score", lambda value: f"{number(value, 2)} ★", 7)
    with category_columns[2]:
        st.plotly_chart(
            bar_chart(
                relationship,
                "delivery_performance",
                "average_review_score",
                "Delivery outcome versus rating",
            ),
            use_container_width=True,
        )

    section_header("Review insights", "Filter-aware score movements, qualifying category rankings, and delivery associations.")
    render_insights(review_insights(filters, metrics, distribution, categories, relationship), columns=3)
    review_alerts=[a for a in build_alerts(filters) if a.metric in {"average_review_score","negative_review_rate","one_star_rate","five_star_rate"}]
    section_header("Review anomalies & opportunities", "Unusual completed-month rating movements with review-volume guardrails.")
    render_alerts(review_alerts,columns=3)

    st.markdown("### Recent negative reviews")
    with st.expander("Open review follow-up table", expanded=False):
        dataframe_panel(get_negative_reviews(filters), height=460)
