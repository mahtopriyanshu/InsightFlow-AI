"""Focused deterministic M17 health-scoring tests."""
import math
from streamlit_app.health.engine import _component,_dimension,_score
def test_score_is_bounded():assert _score(1000,0,1)<=100 and _score(-1000,0,1)>=0
def test_higher_is_better():assert _score(12,10,2,True)>_score(8,10,2,True)
def test_lower_is_better():assert _score(8,10,2,False)>_score(12,10,2,False)
def test_dimension_reweights_available_components():
    a=_component("a","a",10,10,1,.2,"count","r");b=_component("b","b",10,10,1,.8,"count","r");d=_dimension("d",[a,b]);assert abs(d.score-50)<1e-9 and abs(sum(x.weight for x in d.components)-1)<1e-9
def test_no_nan_or_inf():assert math.isfinite(_score(10,10,1))
def test_missing_components_are_unavailable_not_zero():assert _dimension("d",[]).score is None
