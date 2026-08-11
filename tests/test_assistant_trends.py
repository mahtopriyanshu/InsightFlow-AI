"""Governed monthly-trend, causality, and history stabilization tests."""
from datetime import date
from unittest.mock import patch

import pandas as pd

from streamlit_app.assistant.charting import build_answer_chart
from streamlit_app.assistant.formatter import format_answer
from streamlit_app.assistant.history import append_message
from streamlit_app.assistant.models import AnswerEvidence, AssistantAnswer, UnsupportedQuestion
from streamlit_app.assistant.models import AssistantUnavailable
from streamlit_app.assistant.planner import local_plan, provider_plan
from streamlit_app.assistant.semantic import METRICS
from streamlit_app.assistant.sql_generator import generate_query
from streamlit_app.utils.filters import FilterState


TREND_CASES = (
    ("Show the monthly revenue trend.", "payment_revenue", "R$ "),
    ("Show the monthly order trend.", "orders", None),
    ("Show how average order value changed month by month.", "average_order_value", "R$ "),
    ("Show the monthly trend of unique customers.", "unique_customers", None),
    ("Show the monthly delivery rate trend.", "delivery_rate", "%"),
    ("Show how late-delivery rate changed month by month.", "late_delivery_rate", "%"),
    ("Show the monthly average delivery days trend.", "average_delivery_days", " days"),
    ("Show the monthly average review score trend.", "average_review_score", None),
    ("Show the monthly negative-review rate trend.", "negative_review_rate", "%"),
)


def test_monthly_capability_matrix_metadata_and_definitions():
    for question, metric, _ in TREND_CASES:
        plan = local_plan(question)
        assert plan.metadata.metric == metric
        assert (plan.metadata.dimension, plan.metadata.time_grain, plan.metadata.chart_type, plan.metadata.ranking_direction) == ("month", "month", "line", "none")
        assert METRICS[metric].definition


def test_monthly_sql_is_complete_chronological_series():
    filters = FilterState(date(2018, 1, 1), date(2018, 12, 31), ("SP",), ("health_beauty",))
    with patch("streamlit_app.assistant.sql_generator.get_filter_options", return_value=(filters.start_date, filters.end_date, ("SP",), ("health_beauty",))):
        with patch("streamlit_app.assistant.sql_generator.filtered_orders_cte", return_value=("WITH filtered_orders AS (SELECT 1 AS order_id) ", ())):
            for question, metric, _ in TREND_CASES:
                query, effective = generate_query(local_plan(question), filters)
                assert f"AS {metric}" in query.sql
                assert "ORDER BY month" in query.sql
                assert "ORDER BY orders DESC LIMIT 1" not in query.sql
                assert effective == filters


def _answer(question, metric):
    plan = local_plan(question)
    data = pd.DataFrame({"month": [date(2018, 2, 1), date(2018, 1, 1)], metric: [2.0, 1.0]})
    evidence = AnswerEvidence("test", METRICS[metric].definition, "scope", 1, 2, 0)
    return AssistantAnswer(question, plan.intent, plan.interpretation, "scope", "SELECT", (), data, format_answer(plan, data), plan.metadata, evidence)


def test_monthly_charts_are_lines_chronological_and_unit_aware():
    for question, metric, unit in TREND_CASES:
        figure = build_answer_chart(_answer(question, metric))
        assert figure.data[0].type == "scatter"
        assert figure.data[0].x.tolist() == [date(2018, 1, 1), date(2018, 2, 1)]
        assert figure.layout.yaxis.title.text == METRICS[metric].label
        if unit == "R$ ": assert figure.layout.yaxis.tickprefix == unit
        elif unit: assert figure.layout.yaxis.ticksuffix == unit


def test_order_trend_natural_language_variants_are_equivalent():
    variants = ("Show monthly orders.", "How have orders changed month by month?", "Plot orders over time.", "Show the order trend by month.")
    plans = [local_plan(question) for question in variants]
    assert all(plan.intent == "monthly_trend" and plan.metadata.metric == "orders" for plan in plans)


def test_peak_and_trough_month_remain_rankings():
    high = local_plan("Which month had the highest number of orders?")
    low = local_plan("Which month had the lowest number of orders?")
    assert high.intent == low.intent == "peak_orders_month"
    assert high.metadata.ranking_direction == "descending"
    assert low.metadata.ranking_direction == "ascending"
    assert high.metadata.chart_type == low.metadata.chart_type == "table"


def test_multimetric_and_multidimensional_trends_remain_unsupported():
    for question in ("Show monthly revenue and orders.", "Show revenue by category month by month."):
        try: local_plan(question)
        except UnsupportedQuestion: pass
        else: raise AssertionError("Unsupported combination was accepted")


def test_causal_question_is_rejected_with_descriptive_alternative():
    try: local_plan("Why did revenue decrease?")
    except UnsupportedQuestion as exc:
        message = str(exc).lower()
        assert "causal" in message and "observed contributors" in message
        assert "because" not in message
    else: raise AssertionError("Causal question was accepted as a factual analysis")


def test_history_is_append_only_across_success_and_failure_types():
    history = []
    kinds = ["success"] * 5 + ["unsupported", "security", "provider_unavailable", "success"]
    for index, kind in enumerate(kinds):
        append_message(history, {"id": index, "kind": kind})
    assert len(history) == 9
    assert [item["kind"] for item in history] == kinds


def test_provider_failure_remains_distinct_from_semantic_rejection():
    with patch("streamlit_app.assistant.planner.AISettings.from_environment") as settings:
        settings.return_value = type("Settings", (), {"provider": "gemini"})()
        with patch("streamlit_app.assistant.planner._gemini_content", side_effect=TimeoutError):
            try: provider_plan("Show monthly orders.")
            except AssistantUnavailable as exc: assert "temporarily unavailable" in str(exc)
            else: raise AssertionError("Provider failure was not preserved")
