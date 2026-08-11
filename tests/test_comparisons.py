"""Focused M15 comparison behavior tests."""
from streamlit_app.comparisons.engine import build_result
from streamlit_app.comparisons.metrics import compare_metric
from streamlit_app.comparisons.models import ComparisonEvidence

E=ComparisonEvidence("definition",10,9,"SP · health_beauty")
def metric(left,right,dtype="percent",unit="currency",direction="higher"):return compare_metric("Revenue","revenue",left,right,dtype,unit,direction,E)
def test_period_comparison():assert metric(120,100).difference==20
def test_category_comparison():assert build_result("category","A","B",{"x":2},{"x":1},(("X","x","percent","count","higher","d"),),"scope").metrics[0].available
def test_state_comparison():assert metric(90,100).difference==-10
def test_seller_comparison():assert metric(100,80).difference==25
def test_equal_values():assert metric(10,10).difference==0
def test_zero_denominator():assert not metric(10,0).available
def test_missing_value():assert not metric(None,10).available
def test_unsupported_metric_is_unavailable():assert not build_result("x","A","B",{}, {},(("Unknown","unknown","percent","count","neutral","unsupported"),),"scope").metrics[0].available
def test_filter_scope_preserved():assert metric(2,1).evidence.scope=="SP · health_beauty"
def test_correct_units():assert metric(10,5,"days","days").difference_type=="days"
def test_preferred_direction():assert metric(10,5,"percentage_points","percentage","lower").preferred_direction=="lower"
