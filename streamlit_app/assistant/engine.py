"""End-to-end governed question to verified answer pipeline."""
import streamlit as st

from streamlit_app.assistant.executor import execute_read_only
from streamlit_app.assistant.formatter import format_answer
from streamlit_app.assistant.models import AnswerEvidence, AssistantAnswer
from streamlit_app.assistant.planner import local_plan, provider_plan
from streamlit_app.assistant.result_validator import validate_result
from streamlit_app.assistant.semantic import METRICS
from streamlit_app.assistant.sql_generator import generate_query
from streamlit_app.assistant.validator import validate_sql
from streamlit_app.insights.comparisons import scope_label
from streamlit_app.utils.filters import FilterState


@st.cache_data(ttl=300, show_spinner=False)
def ask_assistant(question: str, active_filters: FilterState, *, use_llm: bool = True) -> AssistantAnswer:
    plan = provider_plan(question, active_filters) if use_llm else local_plan(question)
    generated, effective = generate_query(plan, active_filters)
    validate_sql(generated.sql)
    data, execution_ms = execute_read_only(generated.sql, generated.params)
    validate_result(data)
    metric = METRICS[generated.metric_key]
    scope = f"{effective.start_date:%d %b %Y} – {effective.end_date:%d %b %Y} · {scope_label(effective)}"
    evidence = AnswerEvidence(generated.source, metric.definition, scope, execution_ms, len(data), 1 if use_llm else 0)
    warnings = ()
    if generated.metadata.time_grain == "month":
        warnings = ("Boundary months reflect the exact active date scope and may be partial; they are shown descriptively and are not classified as unexplained declines.",)
    return AssistantAnswer(question, plan.intent, plan.interpretation, scope, generated.sql, generated.params, data, format_answer(plan, data), generated.metadata, evidence, warnings)
