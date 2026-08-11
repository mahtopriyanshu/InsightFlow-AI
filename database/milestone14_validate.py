"""Live filter-awareness, evidence, boundary, entity, and timing checks for M14."""
from datetime import date
from pathlib import Path
from time import perf_counter
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from streamlit_app.anomalies import build_alerts
from streamlit_app.services.anomaly_history import get_business_history
from streamlit_app.services.common import get_filter_options
from streamlit_app.services.portfolio import get_category_analytics,get_seller_analytics
from streamlit_app.utils.filters import FilterState

def check(name,filters):
    started=perf_counter();alerts=build_alerts(filters);elapsed=perf_counter()-started
    assert all(a.evidence and a.evidence.historical_periods>=6 for a in alerts)
    assert all(a.period not in {"Sep 2018","Oct 2018"} for a in alerts)
    if filters.states:assert all("SP" in a.scope for a in alerts)
    if filters.categories:assert all(filters.categories[0] in a.scope for a in alerts)
    print(name,{"alerts":len(alerts),"seconds":round(elapsed,3),"items":[(a.period,a.metric,a.category) for a in alerts]})

def main():
    lo,hi,_,categories=get_filter_options();cat="health_beauty" if "health_beauty" in categories else categories[0]
    contexts={"full":FilterState(lo,hi),"date":FilterState(date(2018,1,1),date(2018,6,30)),"SP":FilterState(lo,hi,("SP",)),"category":FilterState(lo,hi,(),(cat,)),"combined":FilterState(date(2018,1,1),date(2018,6,30),("SP",),(cat,))}
    for name,filters in contexts.items():check(name,filters)
    full=contexts["full"]
    cats=tuple(get_category_analytics(full).head(8).category.astype(str));sellers=tuple(get_seller_analytics(full).head(8).seller_id.astype(str))
    category_alerts=build_alerts(full,include_business=False,category_labels=cats,limit=20)
    seller_alerts=build_alerts(full,include_business=False,seller_labels=sellers,limit=20)
    assert all(a.entity_type=="category" for a in category_alerts);assert all(a.entity_type=="seller" for a in seller_alerts)
    print("entities",{"category_alerts":len(category_alerts),"seller_alerts":len(seller_alerts)})
    started=perf_counter();build_alerts(full);print("cached_business_seconds",round(perf_counter()-started,4))
if __name__=="__main__":main()
