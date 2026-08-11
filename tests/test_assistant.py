"""Focused semantic, scope, and answer-model tests."""
from datetime import date
from unittest.mock import patch
import os
from streamlit_app.assistant.config import AISettings
from streamlit_app.assistant.planner import local_plan
from streamlit_app.assistant.sql_generator import effective_filters
from streamlit_app.utils.filters import FilterState


def test_golden_intents_map_deterministically():
    cases={"What is total revenue?":"total_revenue","How many total orders?":"total_orders","How many unique customers do we have?":"unique_customers","What is average order value?":"aov","What are the top 5 categories by revenue?":"top_categories","Which states generate the most revenue?":"top_states","Show monthly revenue trend.":"monthly_revenue","What payment method is used most?":"payment_distribution","What is delivery rate?":"delivery_rate","What is late-delivery rate?":"late_delivery_rate","What is our average review score?":"average_review_score","What is negative-review rate?":"negative_review_rate","Which sellers generate the most merchandise revenue?":"top_sellers","Which categories have poor reviews?":"category_reviews","Compare SP and RJ by revenue.":"compare_states"}
    assert all(local_plan(question).intent==intent for question,intent in cases.items())


def test_active_scope_is_preserved_without_override():
    active=FilterState(date(2018,1,1),date(2018,3,31),("SP",),("health_beauty",));result=effective_filters(active,local_plan("What is revenue?"));assert result==active


def test_explicit_state_scope_overrides_active_state():
    active=FilterState(date(2018,1,1),date(2018,3,31),("MG",));result=effective_filters(active,local_plan("Compare SP and RJ by revenue"));assert result.states==("SP","RJ")


def test_explicit_year_overrides_active_dates():
    active=FilterState(date(2017,1,1),date(2017,12,31));result=effective_filters(active,local_plan("What was revenue in 2018?"));assert result.start_date==date(2018,1,1) and result.end_date==date(2018,12,31)


def test_top_limit_is_bounded(): assert local_plan("Top 500 categories by revenue").limit==25


def test_gemini_is_safe_default_when_key_is_configured():
    environment={"AI_API_KEY":"test-only-placeholder"}
    with patch.dict(os.environ,environment,clear=True):
        settings=AISettings.from_environment()
    assert settings.provider=="gemini" and settings.model=="gemini-3.1-flash-lite"
