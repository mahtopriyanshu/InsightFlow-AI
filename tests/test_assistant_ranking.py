"""Regression tests for governed ranking metadata, charts, and UI keys."""
from datetime import date

import pandas as pd
from unittest.mock import patch

from streamlit_app.assistant.charting import assistant_element_key, build_answer_chart, render_answer_chart
from streamlit_app.assistant.formatter import format_answer
from streamlit_app.assistant.models import AnswerEvidence, AssistantAnswer
from streamlit_app.assistant.planner import local_plan
from streamlit_app.assistant.sql_generator import generate_query
from streamlit_app.utils.filters import FilterState


CASES = (
    ("Show me the top 10 product categories by number of orders.", "top_categories", "orders", "category", "descending", "bar", 10),
    ("Show the top 10 product categories by merchandise revenue.", "top_categories", "merchandise_revenue", "category", "descending", "bar", 10),
    ("Show the 10 lowest performing product categories by merchandise revenue.", "top_categories", "merchandise_revenue", "category", "ascending", "bar", 10),
    ("Which 10 states have the most orders?", "top_states", "orders", "state", "descending", "bar", 10),
    ("Which states have the highest late-delivery rate?", "late_states", "late_delivery_rate", "state", "descending", "bar", 10),
    ("Which categories have the highest average review score?", "category_reviews", "average_review_score", "category", "descending", "bar", 10),
    ("Show monthly revenue trend.", "monthly_revenue", "payment_revenue", "month", "none", "line", 10),
)


def test_requested_metadata_is_canonicalized():
    for question, intent, metric, dimension, direction, chart, limit in CASES:
        plan = local_plan(question)
        assert (plan.intent, plan.metadata.metric, plan.metadata.dimension) == (intent, metric, dimension)
        assert (plan.metadata.ranking_direction, plan.metadata.chart_type, plan.limit) == (direction, chart, limit)


def test_generated_sql_uses_requested_metric_and_direction():
    filters = FilterState(date(2018, 1, 1), date(2018, 12, 31))
    with patch("streamlit_app.assistant.sql_generator.get_filter_options", return_value=(filters.start_date, filters.end_date, ("SP", "RJ"), ("health_beauty",))):
        with patch("streamlit_app.assistant.sql_generator.filtered_orders_cte", return_value=("WITH filtered_orders AS (SELECT 1 AS order_id) ", ())):
            for question, _, metric, _, direction, _, _ in CASES:
                query, _ = generate_query(local_plan(question), filters)
                if direction != "none":
                    assert f"ORDER BY {metric} {'ASC' if direction == 'ascending' else 'DESC'}" in query.sql
                else:
                    assert "ORDER BY month" in query.sql


def _answer(question, data):
    plan = local_plan(question)
    evidence = AnswerEvidence("test", "test metric", "test scope", 1.0, len(data), 0)
    return AssistantAnswer(question, plan.intent, plan.interpretation, "test scope", "SELECT 1", (), data, format_answer(plan, data), plan.metadata, evidence)


def test_category_orders_chart_and_formatter_use_orders():
    answer = _answer(CASES[0][0], pd.DataFrame({"category": ["a", "b"], "merchandise_revenue": [999, 1], "orders": [10, 8]}))
    figure = build_answer_chart(answer)
    assert figure.data[0].x.tolist() == [8, 10]
    assert figure.layout.xaxis.title.text == "Orders"
    assert "order count" in answer.message and "revenue" not in answer.message.lower()


def test_category_revenue_chart_uses_merchandise_revenue():
    answer = _answer(CASES[1][0], pd.DataFrame({"category": ["a", "b"], "merchandise_revenue": [20, 10], "orders": [1, 100]}))
    figure = build_answer_chart(answer)
    assert figure.data[0].x.tolist() == [10, 20]
    assert figure.layout.xaxis.title.text == "Merchandise revenue"


def test_lowest_ranking_wording_is_descriptive():
    answer = _answer(CASES[2][0], pd.DataFrame({"category": ["low", "next"], "merchandise_revenue": [10, 20], "orders": [1, 2]}))
    assert "lowest merchandise revenue" in answer.message.lower()
    assert "leads" not in answer.message.lower()


def test_monthly_chart_is_chronological_and_uses_payment_revenue():
    answer = _answer(CASES[6][0], pd.DataFrame({"month": [date(2018, 2, 1), date(2018, 1, 1)], "payment_revenue": [20, 10], "orders": [2, 1]}))
    figure = build_answer_chart(answer)
    assert figure.data[0].x.tolist() == [date(2018, 1, 1), date(2018, 2, 1)]
    assert figure.layout.yaxis.title.text == "Payment revenue"


def test_streamlit_keys_are_stable_per_instance_and_unique_between_instances():
    answer = _answer(CASES[0][0], pd.DataFrame({"category": ["a", "b"], "merchandise_revenue": [2, 1], "orders": [2, 1]}))
    first = assistant_element_key(answer, "response-1", "chart")
    assert first == assistant_element_key(answer, "response-1", "chart")
    keys = {
        first,
        assistant_element_key(answer, "response-2", "chart"),
        assistant_element_key(answer, "response-1", "table"),
    }
    assert len(keys) == 3
    assert all(key.startswith("assistant_") and len(key) < 80 for key in keys)


def test_repeated_charts_always_pass_distinct_explicit_streamlit_keys():
    answer = _answer(CASES[0][0], pd.DataFrame({"category": ["a", "b"], "merchandise_revenue": [2, 1], "orders": [2, 1]}))
    with patch("streamlit_app.assistant.charting.st.plotly_chart") as plotly_chart:
        render_answer_chart(answer, "response-1")
        render_answer_chart(answer, "response-2")
        render_answer_chart(answer, "response-3")
    keys = [call.kwargs.get("key") for call in plotly_chart.call_args_list]
    assert len(keys) == 3
    assert None not in keys
    assert len(set(keys)) == 3
