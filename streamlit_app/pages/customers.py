"""Customer Intelligence Pro: filter-aware RFM segmentation and profiles."""
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_app.anomalies import build_alerts
from streamlit_app.components.layout import render_alerts

from streamlit_app.charts.factory import bar_chart, pareto_chart, rfm_segment_donut
from streamlit_app.components.layout import (
    dataframe_panel, filter_context, kpi_card, page_header, profile_card,
    render_insights, section_header,
)
from streamlit_app.insights import customer_insights
from streamlit_app.services.customers import (
    get_customer_locations, get_customer_metrics, get_customer_orders,
    get_top_customers, search_customers,
)
from streamlit_app.services.rfm import (
    SEGMENT_COLORS, get_customer_rfm_profile, get_pareto_analysis,
    get_rfm_customers, get_segment_geography, get_segment_summary,
    get_value_matrix_sample,
)
from streamlit_app.utils.filters import FilterState
from streamlit_app.utils.formatting import currency, number, percentage


def _segment_row(summary: pd.DataFrame, segment: str) -> pd.Series | None:
    rows = summary.loc[summary["segment"].astype(str).eq(segment)]
    return None if rows.empty else rows.iloc[0]


def _summary_display(summary: pd.DataFrame) -> pd.DataFrame:
    display = summary[["segment", "customers", "customer_share", "revenue",
                       "revenue_share", "avg_revenue_per_customer", "avg_orders",
                       "avg_recency_days"]].copy()
    display.columns = ["Segment", "Customers", "Customer Share", "Revenue",
                       "Revenue Share", "Avg Revenue / Customer", "Avg Orders",
                       "Avg Recency Days"]
    display["Segment"] = display["Segment"].astype(str)
    display["Customer Share"] = display["Customer Share"].map(percentage)
    display["Revenue"] = display["Revenue"].map(currency)
    display["Revenue Share"] = display["Revenue Share"].map(percentage)
    display["Avg Revenue / Customer"] = display["Avg Revenue / Customer"].map(currency)
    display["Avg Orders"] = display["Avg Orders"].map(lambda value: number(value, 2))
    display["Avg Recency Days"] = display["Avg Recency Days"].map(lambda value: number(value, 1))
    return display


def render(filters: FilterState) -> None:
    """Render explainable customer segmentation, value, geography, and lookup."""
    page_header(
        "Customer Intelligence Pro",
        "Explain customer value, purchase depth, inactivity, and revenue concentration with RFM.",
        "Behavioral Segmentation",
    )
    filter_context(filters.start_date, filters.end_date, filters.states, filters.categories)
    with st.spinner("Building filter-aware customer profiles..."):
        metrics = get_customer_metrics(filters)
        locations = get_customer_locations(filters)
        top_customers = get_top_customers(filters)
        profiles = get_rfm_customers(filters)

    if metrics.empty or profiles.empty:
        st.info("No customer data matches the current filters.")
        return

    row = metrics.iloc[0]
    summary = get_segment_summary(profiles)
    pareto_points, pareto_metrics = get_pareto_analysis(profiles)
    geography = get_segment_geography(profiles)
    champion = _segment_row(summary, "Champions")
    at_risk = _segment_row(summary, "At Risk")

    columns = st.columns(6)
    values = [
        ("Total Customers", number(len(profiles))),
        ("Repeat Rate", percentage(row["repeat_rate"])),
        ("Revenue / Customer", currency(row["revenue_per_customer"])),
        ("Orders / Customer", number(row["orders_per_customer"], 2)),
        ("Champion Customers", number(0 if champion is None else champion["customers"])),
        ("At-Risk Customers", number(0 if at_risk is None else at_risk["customers"])),
    ]
    for column, (label, value) in zip(columns, values):
        with column:
            kpi_card(label, value)

    reference_date = profiles["reference_date"].iloc[0]
    st.caption(
        f"RFM scope: selected orders only · Recency reference date: {reference_date:%d %b %Y} · "
        "At Risk is a historical behavior label, not a churn prediction."
    )

    section_header("RFM portfolio", "Customer mix and revenue contribution use exact customer-level aggregates.")
    mix_columns = st.columns([1, 1, 1.15])
    with mix_columns[0]:
        st.plotly_chart(rfm_segment_donut(summary, "customers", "Customers by RFM segment", SEGMENT_COLORS), use_container_width=True)
    with mix_columns[1]:
        st.plotly_chart(rfm_segment_donut(summary, "revenue", "Revenue by RFM segment", SEGMENT_COLORS), use_container_width=True)
    with mix_columns[2]:
        render_insights(customer_insights(
            filters, metrics, locations, top_customers, summary, pareto_metrics, geography,
        ), columns=1)

    section_header("Customer value matrix", "Recency, monetary value, and purchase frequency reveal behavioral differences.")
    customer_alerts=[a for a in build_alerts(filters) if a.metric in {"unique_customers","repeat_rate","revenue_per_customer"}]
    section_header("Customer anomalies & opportunities", "Unusual completed-month audience and value behavior; not churn prediction.")
    render_alerts(customer_alerts,columns=3)
    matrix = get_value_matrix_sample(profiles)
    matrix_figure = px.scatter(
        matrix, x="recency_days", y="monetary", size="frequency", color="segment",
        color_discrete_map=SEGMENT_COLORS, hover_name="customer_unique_id",
        hover_data={"state": True, "frequency": True, "recency_days": True,
                    "monetary": ":.2f", "segment": True},
        labels={"recency_days": "Recency (days)", "monetary": "Revenue (R$)", "segment": "RFM Segment"},
        title="RFM customer value matrix",
    )
    matrix_figure.update_layout(height=390, margin={"l": 20, "r": 20, "t": 55, "b": 20},
                                paper_bgcolor="white", plot_bgcolor="white")
    matrix_figure.update_yaxes(tickprefix="R$ ", gridcolor="#E2E8F0")
    matrix_figure.update_xaxes(gridcolor="#E2E8F0")
    st.plotly_chart(matrix_figure, use_container_width=True)
    if len(matrix) < len(profiles):
        st.caption(f"Visualization uses a deterministic, segment-balanced sample of {len(matrix):,} customers; all KPIs and tables use all {len(profiles):,} profiles.")

    section_header("Revenue concentration", "Observed concentration—not an assumed 80/20 rule.")
    concentration_columns = st.columns([1.5, .8])
    with concentration_columns[0]:
        st.plotly_chart(pareto_chart(pareto_points, "Cumulative customer value"), use_container_width=True)
    with concentration_columns[1]:
        kpi_card("Customers generating 80%", percentage(pareto_metrics["customers_for_80pct_revenue"]))
        kpi_card("Top 10% revenue share", percentage(pareto_metrics["top_10pct_revenue_share"]))
        st.info("The curve ranks customers by selected-period payment revenue and accumulates their contribution.")

    section_header("Segment profiles", "Reconciled segment behavior and contribution.")
    dataframe_panel(_summary_display(summary), height=340)

    section_header("Priority audiences", "High historical value and inactive high-value behavior are shown separately.")
    audience_columns = st.columns(2)
    high_value = profiles.sort_values(["monetary", "frequency"], ascending=False).head(25)
    high_display = high_value[["customer_unique_id", "segment", "frequency", "monetary",
                               "recency_days", "state", "city"]].copy()
    high_display.columns = ["Customer ID", "RFM Segment", "Orders", "Revenue", "Recency Days", "State", "City"]
    high_display["Revenue"] = high_display["Revenue"].map(currency)
    with audience_columns[0]:
        st.markdown("#### High-value customers")
        dataframe_panel(high_display.head(12), height=410)
        with st.expander("View Top 25 high-value customers"):
            dataframe_panel(high_display, height=430)
    with audience_columns[1]:
        st.markdown("#### At Risk according to historical RFM")
        risk_profiles = profiles.loc[profiles["segment"].eq("At Risk")].sort_values("monetary", ascending=False)
        if risk_profiles.empty:
            st.info("No customers meet the At Risk rules in this filter scope.")
        else:
            risk_cols = st.columns(3)
            risk_values = [
                ("Customers", number(len(risk_profiles))),
                ("Historical Revenue", currency(risk_profiles["monetary"].sum())),
                ("Avg Recency", f"{risk_profiles['recency_days'].mean():.0f} days"),
            ]
            for risk_col, (label, value) in zip(risk_cols, risk_values):
                with risk_col: kpi_card(label, value)
            risk_display = risk_profiles[["customer_unique_id", "frequency", "monetary",
                                          "recency_days", "state"]].head(15).copy()
            risk_display.columns = ["Customer ID", "Orders", "Historical Revenue", "Recency Days", "State"]
            risk_display["Historical Revenue"] = risk_display["Historical Revenue"].map(currency)
            dataframe_panel(risk_display, height=300)

    section_header("RFM geography", "Only state/segment groups with at least 25 customers are ranked.")
    geo_columns = st.columns(2)
    for column, segment, title in (
        (geo_columns[0], "Champions", "Champion customers by state"),
        (geo_columns[1], "At Risk", "At-Risk customers by state"),
    ):
        with column:
            subset = geography.loc[geography["segment"].astype(str).eq(segment)].head(12)
            if subset.empty:
                st.info(f"No {segment} state group meets the 25-customer threshold.")
            else:
                st.plotly_chart(bar_chart(subset.sort_values("customers"), "state", "customers", title, horizontal=True), use_container_width=True)

    section_header("Customer lookup", "Search a stable customer identity and inspect its selected-scope RFM profile.")
    search_term = st.text_input("Search customer_unique_id", placeholder="Paste or type part of a customer identifier")
    if search_term.strip():
        results = search_customers(search_term)
        if results.empty:
            st.info("No matching customer identifier was found.")
        else:
            selected = st.selectbox("Open customer profile", results["customer_unique_id"].tolist())
            profile = results.loc[results["customer_unique_id"].eq(selected)].iloc[0]
            selected_rfm = get_customer_rfm_profile(profiles, selected)
            fields = [
                ("All-history Orders", number(profile["order_count"])),
                ("All-history Revenue", currency(profile["total_revenue"])),
                ("Location", f"{profile['customer_city']}, {profile['customer_state']}"),
            ]
            if not selected_rfm.empty:
                rfm = selected_rfm.iloc[0]
                fields.extend([
                    ("Selected-scope Segment", str(rfm["segment"])),
                    ("R / F / M Scores", f"{rfm['r_score']} / {rfm['f_score']} / {rfm['m_score']}"),
                    ("Selected-scope Recency", f"{rfm['recency_days']} days"),
                    ("Selected-scope Orders", number(rfm["frequency"])),
                    ("Selected-scope Revenue", currency(rfm["monetary"])),
                ])
            else:
                fields.append(("Selected-scope RFM", "Outside current filter context"))
            profile_card("Customer profile", str(selected), fields, "♙")
            with st.expander("View all matching customers"):
                dataframe_panel(results, height=260)
            st.markdown("#### Complete order history")
            dataframe_panel(get_customer_orders(selected), height=360)
