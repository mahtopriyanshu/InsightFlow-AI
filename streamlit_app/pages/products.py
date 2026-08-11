"""Product Intelligence Pro decision-support dashboard."""
import plotly.express as px
import streamlit as st
from streamlit_app.anomalies import build_alerts
from streamlit_app.components.layout import render_alerts

from streamlit_app.charts.factory import bar_chart, pareto_chart
from streamlit_app.components.layout import dataframe_panel, filter_context, kpi_card, page_header, profile_card, render_insights, section_header
from streamlit_app.insights import product_pro_insights
from streamlit_app.services.portfolio import (
    MIN_CATEGORY_ORDERS, MIN_CATEGORY_REVIEWS, category_signals, concentration,
    get_category_analytics, get_category_seller_concentration, get_product_analytics,
)
from streamlit_app.utils.filters import FilterState
from streamlit_app.utils.formatting import currency, number, percentage


def render(filters: FilterState) -> None:
    page_header("Product Intelligence Pro", "Connect merchandise economics, customer experience, fulfillment, freight, and supplier concentration.", "Portfolio Decision Support")
    filter_context(filters.start_date, filters.end_date, filters.states, filters.categories)
    with st.spinner("Building grain-safe product intelligence..."):
        categories=get_category_analytics(filters); products=get_product_analytics(filters)
        supplier=get_category_seller_concentration(filters)
    if categories.empty:return st.info("No product activity matches the current filters.")
    cat_curve,cat_conc=concentration(categories,"merchandise_revenue")
    prod_curve,prod_conc=concentration(products,"merchandise_revenue")
    signals=category_signals(categories)
    top=categories.iloc[0]
    values=[("Products",number(len(products))), ("Categories",number(len(categories))),
      ("Merchandise Revenue",currency(categories.merchandise_revenue.sum())),
      ("Units Sold",number(categories.units.sum())),
      ("Freight / Merchandise",percentage(100*categories.freight.sum()/categories.merchandise_revenue.sum())),
      ("Top Category",str(top.category))]
    for col,(label,value) in zip(st.columns(6),values):
        with col:kpi_card(label,value)
    st.caption("Revenue means item-price merchandise revenue, not payment revenue. Reviews and delivery are deduplicated once per order–entity.")

    section_header("Category contribution", "Revenue, demand, and cumulative concentration across the selected portfolio.")
    cols=st.columns([1.2,1])
    with cols[0]:st.plotly_chart(bar_chart(categories.head(15).sort_values("merchandise_revenue"),"category","merchandise_revenue","Category merchandise revenue",horizontal=True),use_container_width=True)
    with cols[1]:st.plotly_chart(pareto_chart(cat_curve,"Category cumulative revenue contribution"),use_container_width=True)
    chips=st.columns(4)
    for col,(label,value) in zip(chips,[("Categories for 80%",percentage(cat_conc["entities_for_80"])),("Top 5 category share",percentage(cat_conc["top_5_share"])),("Products for 80%",percentage(prod_conc["entities_for_80"])),("Top 10% product share",percentage(prod_conc["top_10pct_share"]))]):
        with col:kpi_card(label,value)

    section_header("Commercial vs experience", f"Qualifying categories have ≥{MIN_CATEGORY_ORDERS} orders and ≥{MIN_CATEGORY_REVIEWS} reviews; lines use median revenue and review-weighted average score.")
    qualifying=signals.copy()
    if not qualifying.empty:
        fig=px.scatter(qualifying,x="merchandise_revenue",y="average_review_score",size="orders",color="signal",hover_name="category",
          hover_data={"orders":True,"reviews":True,"late_rate":":.1f","freight_ratio":":.1f"},title="Category commercial–experience matrix")
        fig.add_vline(x=qualifying.attrs["revenue_median"],line_dash="dot");fig.add_hline(y=qualifying.attrs["review_benchmark"],line_dash="dot")
        fig.update_layout(height=420,margin={"l":20,"r":20,"t":55,"b":20},paper_bgcolor="white",plot_bgcolor="white")
        fig.update_xaxes(tickprefix="R$ ",gridcolor="#E2E8F0");fig.update_yaxes(gridcolor="#E2E8F0")
        st.plotly_chart(fig,use_container_width=True)

    section_header("Investigation & opportunity signals", "Relative, deterministic signals—not recommendations or causal diagnoses.")
    signal_cols=st.columns(2)
    with signal_cols[0]:
        watch=signals.loc[signals.signal.isin(["Experience Risk","Fulfillment Watch","Freight Watch"])].sort_values("merchandise_revenue",ascending=False)
        st.markdown("#### Needs investigation");dataframe_panel(watch[["category","signal","orders","merchandise_revenue","average_review_score","late_rate","freight_ratio"]].head(15),height=360)
    with signal_cols[1]:
        opportunity=signals.loc[signals.signal.eq("Opportunity Signal")].sort_values("orders",ascending=False)
        st.markdown("#### Opportunity signals");dataframe_panel(opportunity[["category","orders","merchandise_revenue","average_review_score","late_rate"]].head(15),height=360)

    section_header("Freight & supplier concentration", "Freight burden and category reliance on the largest sellers.")
    freight=signals.sort_values("freight_ratio",ascending=False).head(15).sort_values("freight_ratio")
    supplier_major=supplier.loc[supplier.category_revenue>=supplier.category_revenue.median()].sort_values("top_5_seller_share",ascending=False)
    fcols=st.columns(2)
    with fcols[0]:st.plotly_chart(bar_chart(freight,"category","freight_ratio","Freight-to-merchandise ratio (%)",horizontal=True),use_container_width=True)
    with fcols[1]:st.plotly_chart(bar_chart(supplier_major.head(15).sort_values("top_5_seller_share"),"category","top_5_seller_share","Top-5 seller share in major categories",horizontal=True),use_container_width=True)

    section_header("Product insights", "M11 evidence cards now include concentration, experience, and freight signals.")
    render_insights(product_pro_insights(filters,categories,cat_conc,signals),columns=3)
    labels=tuple(categories.head(8).category.astype(str))
    section_header("Category anomalies & opportunities", "Major-category movements outside their own completed-month historical variation.")
    render_alerts(build_alerts(filters,include_business=False,category_labels=labels,limit=5),columns=3)
    with st.expander("Open category and product performance tables"):
        tabs=st.tabs(["Categories","Products","Category seller concentration"])
        with tabs[0]:dataframe_panel(categories,height=460)
        with tabs[1]:dataframe_panel(products.head(1000),height=460)
        with tabs[2]:dataframe_panel(supplier,height=460)

    section_header("Product search", "Search within the active date, destination-state, and category context.")
    term=st.text_input("Search product ID or category",placeholder="Type a product ID or category")
    if term.strip():
        mask=products.product_id.str.contains(term.strip(),case=False,na=False)|products.category.astype(str).str.contains(term.strip(),case=False,na=False)
        results=products.loc[mask].head(100)
        if results.empty:st.info("No products match within the current filter context.")
        else:
            selected=st.selectbox("Open product profile",results.product_id.tolist());p=results.loc[results.product_id.eq(selected)].iloc[0]
            profile_card("Product profile",str(selected),[("Category",str(p.category)),("Orders",number(p.orders)),("Units",number(p.units)),("Merchandise Revenue",currency(p.merchandise_revenue)),("Average Item Price",currency(p.average_item_price)),("Freight",currency(p.freight)),("Average Review",number(p.average_review_score,2)),("Review Count",number(p.reviews)),("Late Rate",percentage(p.late_rate))],"▣")
            with st.expander("View matching products"):dataframe_panel(results,height=360)
