"""Seller Intelligence Pro decision-support dashboard."""
import plotly.express as px
import pandas as pd
import streamlit as st
from streamlit_app.anomalies import build_alerts
from streamlit_app.components.layout import render_alerts

from streamlit_app.charts.factory import bar_chart, pareto_chart
from streamlit_app.components.layout import dataframe_panel,filter_context,kpi_card,page_header,profile_card,render_insights,section_header
from streamlit_app.insights import seller_pro_insights
from streamlit_app.services.portfolio import MIN_SELLER_ORDERS,concentration,get_seller_analytics,seller_signals
from streamlit_app.utils.filters import FilterState
from streamlit_app.utils.formatting import currency,number,percentage


def render(filters:FilterState)->None:
    page_header("Seller Intelligence Pro","Evaluate marketplace contribution, fulfillment exposure, geography, and concentration.","Marketplace Decision Support")
    filter_context(filters.start_date,filters.end_date,filters.states,filters.categories)
    with st.spinner("Building grain-safe seller intelligence..."): sellers=get_seller_analytics(filters)
    if sellers.empty:return st.info("No seller activity matches the current filters.")
    numeric_columns=["orders","units","merchandise_revenue","average_item_value","freight","reviews","average_review_score","delivered_orders","eligible_deliveries","late_rate","average_delivery_days","delivery_rate"]
    sellers[numeric_columns]=sellers[numeric_columns].apply(pd.to_numeric,errors="coerce")
    curve,conc=concentration(sellers,"merchandise_revenue");signals=seller_signals(sellers);top=sellers.iloc[0]
    weighted_late=100*sellers.eligible_deliveries.mul(sellers.late_rate.fillna(0)/100).sum()/max(sellers.eligible_deliveries.sum(),1)
    values=[("Active Sellers",number(len(sellers))),("Merchandise Revenue",currency(sellers.merchandise_revenue.sum())),("Orders Served",number(sellers.orders.sum())),("Units Sold",number(sellers.units.sum())),("Eligible Late Rate",percentage(weighted_late)),("Top Seller Share",percentage(100*top.merchandise_revenue/sellers.merchandise_revenue.sum()))]
    for col,(label,value) in zip(st.columns(6),values):
        with col:kpi_card(label,value)
    st.caption("Customer-state filters represent destination market context. Seller geography always uses seller_state. Reviews are an order-level experience proxy attributed once per order–seller.")

    section_header("Seller leaderboard","Rank sellers by merchandise revenue, order volume, and fulfillment exposure.")
    metric=st.selectbox("Rank leaderboard by",["Merchandise Revenue","Orders","Units","Lowest Late Rate"],label_visibility="collapsed")
    key={"Merchandise Revenue":"merchandise_revenue","Orders":"orders","Units":"units","Lowest Late Rate":"late_rate"}[metric]
    ranked=sellers.loc[sellers.orders>=MIN_SELLER_ORDERS] if key=="late_rate" else sellers
    ranked=ranked.sort_values(key,ascending=(key=="late_rate")).head(20)
    dataframe_panel(ranked[["seller_id","state","city","merchandise_revenue","orders","units","delivery_rate","late_rate","average_delivery_days"]],height=430)

    section_header("Revenue concentration","Observed seller dependence—not an assumed Pareto rule.")
    cols=st.columns([1.35,.8])
    with cols[0]:st.plotly_chart(pareto_chart(curve,"Cumulative seller revenue contribution"),use_container_width=True)
    with cols[1]:
        kpi_card("Sellers generating 80%",percentage(conc["entities_for_80"]));kpi_card("Top 10 seller share",percentage(conc["top_10_share"]));kpi_card("Top 10% seller share",percentage(conc["top_10pct_share"]))

    section_header("Commercial vs fulfillment",f"Sellers require ≥{MIN_SELLER_ORDERS} orders; reference lines use qualifying medians.")
    if not signals.empty:
        fig=px.scatter(signals,x="merchandise_revenue",y="late_rate",size="orders",color="signal",hover_name="seller_id",hover_data={"state":True,"orders":True,"average_review_score":":.2f"},title="Seller revenue–fulfillment matrix")
        fig.add_vline(x=signals.attrs["revenue_median"],line_dash="dot");fig.add_hline(y=signals.attrs["late_median"],line_dash="dot")
        fig.update_layout(height=420,margin={"l":20,"r":20,"t":55,"b":20},paper_bgcolor="white",plot_bgcolor="white")
        fig.update_xaxes(tickprefix="R$ ",gridcolor="#E2E8F0");fig.update_yaxes(ticksuffix="%",gridcolor="#E2E8F0")
        st.plotly_chart(fig,use_container_width=True)

    section_header("Operational signals","Meaningful revenue exposure with above-benchmark late delivery is flagged for investigation.")
    risk=signals.loc[signals.signal.ne("Balanced")].sort_values("merchandise_revenue",ascending=False)
    risk_cols=st.columns([1.2,1])
    with risk_cols[0]:dataframe_panel(risk[["seller_id","state","signal","orders","merchandise_revenue","late_rate","average_review_score"]].head(20),height=400)
    state=sellers.groupby("state",as_index=False).agg(sellers=("seller_id","nunique"),revenue=("merchandise_revenue","sum"),orders=("orders","sum"),eligible=("eligible_deliveries","sum"),late_weight=("late_rate",lambda x:0))
    state["revenue_per_seller"]=state.revenue/state.sellers
    with risk_cols[1]:st.plotly_chart(bar_chart(state.sort_values("revenue",ascending=False).head(15).sort_values("revenue"),"state","revenue","Seller-location revenue by state",horizontal=True),use_container_width=True)

    section_header("Seller insights","M11 evidence cards include concentration, fulfillment exposure, and seller geography.")
    render_insights(seller_pro_insights(filters,sellers,conc,signals),columns=3)
    labels=tuple(sellers.head(8).seller_id.astype(str))
    section_header("Seller anomalies & opportunities", "Major-seller completed-month deviations with minimum active-history and order guardrails.")
    render_alerts(build_alerts(filters,include_business=False,seller_labels=labels,limit=5),columns=3)
    with st.expander("Open full seller performance table"):dataframe_panel(sellers,height=500)

    section_header("Seller search","Search within the active order/destination/category scope; location remains seller geography.")
    term=st.text_input("Search seller ID or city",placeholder="Type a seller identifier or city")
    if term.strip():
        mask=sellers.seller_id.str.contains(term.strip(),case=False,na=False)|sellers.city.astype(str).str.contains(term.strip(),case=False,na=False)
        results=sellers.loc[mask].head(50)
        if results.empty:st.info("No sellers match within the current filter context.")
        else:
            selected=st.selectbox("Open seller profile",results.seller_id.tolist());s=results.loc[results.seller_id.eq(selected)].iloc[0]
            profile_card("Seller profile",str(selected),[("Seller Location",f"{s.city}, {s.state}"),("Orders",number(s.orders)),("Units",number(s.units)),("Merchandise Revenue",currency(s.merchandise_revenue)),("Revenue Share",percentage(100*s.merchandise_revenue/sellers.merchandise_revenue.sum())),("Freight",currency(s.freight)),("Late Rate",percentage(s.late_rate)),("Avg Delivery Days",number(s.average_delivery_days,1)),("Review Proxy",number(s.average_review_score,2))],"♧")
            with st.expander("View matching sellers"):dataframe_panel(results,height=360)
