"""Focused deterministic concentration and signal tests for M13."""
import pandas as pd

from streamlit_app.services.portfolio import concentration,category_signals,seller_signals


def test_concentration_is_exact_and_monotonic():
    frame=pd.DataFrame({"name":["a","b","c","d"],"value":[80.,10.,5.,5.]})
    curve,metrics=concentration(frame,"value")
    assert metrics["entities_for_80"]==25.0
    assert metrics["top_5_share"]==100.0
    assert curve.revenue_share.is_monotonic_increasing


def test_category_signals_use_qualified_benchmarks():
    frame=pd.DataFrame({"category":["a","b","c","d"],"orders":[100,100,100,5],"reviews":[100,100,100,5],"merchandise_revenue":[1000.,900.,100.,5000.],"average_review_score":[3.,5.,5.,1.],"freight_ratio":[10.,10.,30.,50.],"late_rate":[5.,5.,5.,50.]})
    result=category_signals(frame)
    assert "d" not in result.category.tolist()
    assert result.loc[result.category.eq("a"),"signal"].iloc[0]=="Experience Risk"


def test_seller_risk_requires_minimum_orders():
    frame=pd.DataFrame({"seller_id":["a","b","tiny"],"orders":[100,100,1],"merchandise_revenue":[1000.,100.,9999.],"late_rate":[20.,1.,100.]})
    result=seller_signals(frame)
    assert "tiny" not in result.seller_id.tolist()
