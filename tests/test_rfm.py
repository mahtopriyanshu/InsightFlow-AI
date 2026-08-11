"""Focused correctness tests for deterministic RFM scoring and segmentation."""
import pandas as pd

from streamlit_app.services.rfm import (
    assign_segments, frequency_score, get_pareto_analysis,
    get_segment_summary, percentile_score,
)


def test_ties_receive_identical_scores_and_directions_are_correct():
    values = pd.Series([10, 10, 20, 40, 80])
    monetary = percentile_score(values)
    recency = percentile_score(values, lower_is_better=True)
    assert monetary.iloc[0] == monetary.iloc[1]
    assert recency.iloc[0] == recency.iloc[1]
    assert monetary.iloc[-1] > monetary.iloc[0]
    assert recency.iloc[-1] < recency.iloc[0]


def test_frequency_bands_are_tie_safe_and_count_distinct_orders_semantic():
    assert frequency_score(pd.Series([1, 2, 3, 4, 5, 17])).tolist() == [1, 2, 3, 4, 5, 5]


def test_segments_are_mutually_exclusive_and_exhaustive():
    frame = pd.DataFrame({
        "r_score": [5, 4, 5, 2, 1, 3],
        "f_score": [5, 3, 1, 2, 1, 1],
        "m_score": [5, 4, 2, 5, 1, 4],
    })
    segments = assign_segments(frame)
    assert len(segments) == len(frame)
    assert segments.notna().all()
    assert segments.iloc[0] == "Champions"
    assert segments.iloc[3] == "At Risk"


def test_segment_and_pareto_reconciliation():
    profiles = pd.DataFrame({
        "customer_unique_id": ["a", "b", "c", "d"],
        "segment": ["Champions", "Champions", "At Risk", "Hibernating"],
        "monetary": [80.0, 10.0, 5.0, 5.0],
        "frequency": [5, 2, 1, 1],
        "recency_days": [1, 5, 100, 200],
    })
    summary = get_segment_summary(profiles)
    assert summary["customers"].sum() == len(profiles)
    assert abs(summary["revenue"].sum() - profiles["monetary"].sum()) < 1e-9
    _, metrics = get_pareto_analysis(profiles)
    assert metrics["customers_for_80pct_revenue"] == 25.0
    assert metrics["top_10pct_revenue_share"] == 80.0
