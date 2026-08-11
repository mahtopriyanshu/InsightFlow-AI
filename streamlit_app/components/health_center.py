"""Executive Business Health & Recommendation Center UI."""
import streamlit as st
from streamlit_app.components.layout import health_indicator,insight_card,kpi_card,section_header
from streamlit_app.health.models import HealthReport
from streamlit_app.utils.formatting import currency,number,percentage

def _fmt(value,unit):
    if unit=="currency":return currency(value)
    if unit=="percentage":return percentage(value)
    if unit=="days":return f"{number(value,1)} days"
    if unit=="score":return f"{number(value,2)} / 5"
    return number(value)
def _signals(items,columns=3):
    if not items:return st.info("No evidence-backed item met the current guardrails.")
    cols=st.columns(min(columns,len(items)))
    for index,item in enumerate(items):
        with cols[index%len(cols)]:
            insight_card(item.title,item.message,"!" if item.kind=="risk" else "+",severity=item.severity,supporting_label=item.evidence.current_value)
            with st.expander("View evidence"):
                e=item.evidence;st.markdown(f"**Current:** {e.current_value}  \n**Reference:** {e.reference_value or 'Unavailable'}  \n**Period:** {e.period}  \n**Sample:** {e.sample_size or 'Unavailable'}  \n**Scope:** {e.scope}  \n**Source:** {e.source_module}  \n**Reason:** {e.reason}")
def render_health_center(report:HealthReport):
    section_header("Business Health & Recommendation Center","Transparent filter-aware scores, risks, opportunities, and evidence-backed investigations.")
    overall,dimensions=st.columns([.8,2.2])
    with overall:kpi_card("Overall Business Health",f"{report.overall.score:.0f} / 100",note=report.overall.band)
    with dimensions:
        cols=st.columns(4)
        for col,dimension in zip(cols,report.dimensions):
            with col:health_indicator(dimension.name,float(dimension.score or 0),f"{dimension.score:.0f}" if dimension.score is not None else "N/A",dimension.band)
    with st.expander("How are these scores calculated?"):
        for dimension in report.dimensions:
            st.markdown(f"#### {dimension.name}: {dimension.score:.1f}/100 ({dimension.band})")
            for component in dimension.components:
                st.markdown(f"- **{component.name}:** observed {_fmt(component.observed,component.unit)}; reference {_fmt(component.benchmark,component.unit)}; component score {component.score:.1f}; normalized weight {component.weight:.0%}; contribution {component.contribution:.1f}. {component.reason}.")
    tabs=st.tabs(["Top Risks","Top Opportunities","Recommended Investigations"])
    with tabs[0]:_signals(report.risks)
    with tabs[1]:_signals(report.opportunities)
    with tabs[2]:_signals(report.recommendations)
