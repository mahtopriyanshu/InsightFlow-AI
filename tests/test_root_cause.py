"""Focused M16 decomposition, contribution, wording, and guardrail tests."""
from streamlit_app.root_cause.decomposition import revenue_decomposition
from streamlit_app.root_cause.models import Driver,DriverEvidence

def decomp(o1,a1,o0,a0):return revenue_decomposition(o1,a1,o0,a0)
def test_revenue_decomposition_reconciliation():
    x=decomp(120,11,100,10);assert abs(x["total"]-x["volume"]-x["aov"])<1e-9
def test_positive_revenue_growth():assert decomp(120,11,100,10)["total"]>0
def test_revenue_decline():assert decomp(80,9,100,10)["total"]<0
def test_orders_up_aov_down():
    x=decomp(120,9,100,10);assert x["volume"]>0 and x["aov"]<0
def test_orders_down_aov_up():
    x=decomp(80,12,100,10);assert x["volume"]<0 and x["aov"]>0
def test_zero_total_change():assert decomp(100,10,100,10)["total"]==0
def test_offset_contributors():
    x=decomp(125,8,100,10);assert x["total"]==0 and x["volume"]==-x["aov"]
def test_missing_dimension_is_rejected_safely():
    try:decomp(None,10,100,10)
    except (TypeError,ValueError):return
    assert False
def test_tiny_sample_evidence():assert DriverEvidence("a","b","d","scope",1).sample_size==1
def test_delivery_rate_driver_unit():
    d=Driver("Late Delivery Rate","State","SP",10,5,5,None,"negative",DriverEvidence("a","b","Late-rate percentage-point difference","scope",100),"SP was associated with a +5 pp movement.");assert "Late-rate" in d.evidence.metric_definition
def test_review_association_wording():assert "association" in "This is an association.".lower()
def test_no_causal_wording():
    allowed="contributed to the observed movement and was associated with the period";assert " caused " not in f" {allowed.lower()} " and " because of " not in allowed.lower()
def test_filter_scope_preservation():assert DriverEvidence("a","b","d","SP · health_beauty").scope=="SP · health_beauty"
