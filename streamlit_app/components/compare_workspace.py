"""Premium interactive M15 comparison and M16 explanation workspace."""
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_app.components.layout import dataframe_panel,kpi_card,section_header
from streamlit_app.services.common import get_filter_options
from streamlit_app.services.comparisons import compare_categories,compare_periods,compare_sellers,compare_states
from streamlit_app.services.portfolio import get_seller_analytics
from streamlit_app.root_cause import analyze_change
from streamlit_app.utils.formatting import currency,number,percentage

def _value(metric,value):
    if value is None:return "Unavailable"
    if metric.unit=="currency":return currency(value)
    if metric.unit=="percentage":return percentage(value)
    if metric.unit=="days":return f"{number(value,1)} days"
    if metric.unit=="score":return number(value,2)
    return number(value)
def _delta(metric):
    if metric.difference is None:return "Comparable value unavailable"
    if metric.difference_type=="percent":return f"{metric.difference:+.1f}%"
    if metric.difference_type=="percentage_points":return f"{metric.difference:+.1f} pp"
    if metric.difference_type=="days":return f"{metric.difference:+.1f} days"
    if metric.difference_type=="points":return f"{metric.difference:+.2f} pts"
    return f"{metric.difference:+,.2f}"

def _render_result(result):
    if not result.available:return st.warning(result.reason or "Comparable period unavailable")
    st.markdown(f"#### {result.left_label}  **vs**  {result.right_label}")
    available=[m for m in result.metrics if m.available]
    for start in range(0,len(available),3):
        for col,metric in zip(st.columns(3),available[start:start+3]):
            with col:
                left,right=st.columns(2)
                with left:kpi_card(result.left_label,_value(metric,metric.left_value),note=metric.name)
                with right:kpi_card(result.right_label,_value(metric,metric.right_value),note=metric.name)
                st.caption(f"Gap: **{_delta(metric)}**")
                with st.expander("Comparison evidence"):
                    e=metric.evidence;st.markdown(f"**Definition:** {e.metric_definition}\n\n**Left sample:** {e.left_sample or 'Unavailable'}  \n**Right sample:** {e.right_sample or 'Unavailable'}  \n**Scope:** {e.scope}  \n**Source:** {e.source}")
    section_header("Key differences","Deterministic observations calculated from the displayed metrics.")
    for text in result.observations:st.info(text)
    chart=pd.DataFrame([{"Metric":m.name,result.left_label:m.left_value,result.right_label:m.right_value} for m in available if m.unit in {"currency","count"}]).melt("Metric",var_name="Side",value_name="Value")
    if not chart.empty:st.plotly_chart(px.bar(chart,x="Metric",y="Value",color="Side",barmode="group",title="Comparable commercial scale"),use_container_width=True)

def _render_explanation(filters):
    kpi=st.selectbox("KPI to explain",["Revenue","Orders","Delivery","Reviews","Customers"],key="explain_kpi")
    analysis=analyze_change(filters,kpi)
    if not analysis.available:return st.warning(analysis.reason or "Comparable period unavailable")
    cols=st.columns(3)
    with cols[0]:kpi_card("Current",currency(analysis.current_value) if "Revenue" in analysis.kpi else number(analysis.current_value,2),note=analysis.kpi)
    with cols[1]:kpi_card("Previous",currency(analysis.comparison_value) if "Revenue" in analysis.kpi else number(analysis.comparison_value,2),note=analysis.kpi)
    with cols[2]:kpi_card("Observed Change",currency(analysis.total_change) if "Revenue" in analysis.kpi else number(analysis.total_change,2),note="Not a causal estimate")
    for text in analysis.narrative:st.info(text)
    if not analysis.drivers:return st.info("No reliable bounded drivers were available.")
    rows=pd.DataFrame([{"Dimension":d.dimension,"Entity":d.entity,"Observed contribution":d.absolute_contribution,"Direction":d.direction,"Wording":d.wording} for d in analysis.drivers])
    section_header("What contributed to the change?","Positive offsets and negative drivers are shown separately; observational data does not prove causation.")
    fig=px.bar(rows.head(15).sort_values("Observed contribution"),x="Observed contribution",y="Entity",color="Direction",orientation="h",facet_row="Dimension",title="Observed driver contributions")
    fig.update_layout(height=max(420,120*rows.Dimension.nunique()),showlegend=True)
    st.plotly_chart(fig,use_container_width=True)
    dataframe_panel(rows,height=420)
    with st.expander("Evidence and methodology"):
        first=analysis.drivers[0].evidence
        st.markdown(f"**Current period:** {first.current_period}  \n**Comparison period:** {first.comparison_period}  \n**Scope:** {first.scope}  \n**Source:** {first.source}  \n\nDriver wording uses contribution/association language and does not establish cause.")

def render_compare_workspace(filters):
    """Render opt-in comparison and explanation tools without slowing normal views."""
    section_header("Compare & Explain","Move from what happened, to how it compares, to observed contributing factors.")
    if not st.toggle("Enable interactive Compare Mode",value=False,key="enable_compare_mode"):
        st.caption("Enable to load verified comparison and driver-analysis queries.");return
    compare_tab,explain_tab=st.tabs(["Compare Mode","Explain KPI Change"])
    with compare_tab:
        mode=st.selectbox("Compare type",["Period vs Period","Category vs Category","Destination State vs State","Seller vs Seller"])
        _,_,states,categories=get_filter_options()
        if mode=="Period vs Period":result=compare_periods(filters)
        elif mode=="Category vs Category":
            left,right=st.columns(2)
            with left:a=st.selectbox("Category A",categories,index=categories.index("health_beauty") if "health_beauty" in categories else 0)
            with right:b=st.selectbox("Category B",categories,index=categories.index("computers_accessories") if "computers_accessories" in categories else min(1,len(categories)-1))
            result=compare_categories(filters,a,b) if a!=b else None
        elif mode=="Destination State vs State":
            left,right=st.columns(2)
            with left:a=st.selectbox("Destination state A",states,index=states.index("SP") if "SP" in states else 0)
            with right:b=st.selectbox("Destination state B",states,index=states.index("RJ") if "RJ" in states else min(1,len(states)-1))
            result=compare_states(filters,a,b) if a!=b else None
        else:
            seller_ids=get_seller_analytics(filters).head(100).seller_id.astype(str).tolist();left,right=st.columns(2)
            with left:a=st.selectbox("Seller A",seller_ids,index=0)
            with right:b=st.selectbox("Seller B",seller_ids,index=min(1,len(seller_ids)-1))
            result=compare_sellers(filters,a,b) if a!=b else None
        if result is None:st.warning("Choose two different entities.")
        else:_render_result(result)
    with explain_tab:_render_explanation(filters)
