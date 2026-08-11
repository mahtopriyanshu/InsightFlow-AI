"""Live filter, mode, driver, reconciliation, and performance validation for M15/M16."""
from datetime import date
from pathlib import Path
from time import perf_counter
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from streamlit_app.root_cause import analyze_change
from streamlit_app.services.comparisons import compare_categories,compare_periods,compare_sellers,compare_states
from streamlit_app.services.common import get_filter_options
from streamlit_app.services.portfolio import get_seller_analytics
from streamlit_app.utils.filters import FilterState

def validate(name,filters):
    started=perf_counter();period=compare_periods(filters);period_s=perf_counter()-started
    category=compare_categories(filters,"health_beauty","computers_accessories")
    state=compare_states(filters,"SP","RJ")
    seller_rows=get_seller_analytics(filters).head(2);seller=compare_sellers(filters,*seller_rows.seller_id.astype(str).tolist())
    for result in (category,state,seller):
        assert result.available and result.metrics and all(m.evidence.scope for m in result.metrics)
        assert all(m.difference_type in {"percent","percentage_points","days","points","absolute","unavailable"} for m in result.metrics)
    if filters.states:assert "SP" in category.scope or "state" in name.lower()
    if filters.categories:assert category.left_label=="health_beauty"
    analysis=analyze_change(filters,"Revenue")
    if period.available:
        assert analysis.available
        factors=[d for d in analysis.drivers if d.dimension in {"Order volume","Average order value"}]
        assert abs(sum(d.absolute_contribution for d in factors)-float(analysis.total_change))<.01
        assert all(" caused " not in f" {d.wording.lower()} " and " because of " not in d.wording.lower() for d in analysis.drivers)
    print(name,{"period_available":period.available,"period_seconds":round(period_s,3),"category_metrics":sum(m.available for m in category.metrics),"state_metrics":sum(m.available for m in state.metrics),"seller_metrics":sum(m.available for m in seller.metrics),"drivers":len(analysis.drivers) if analysis.available else 0,"revenue_change":round(float(analysis.total_change),2) if analysis.available else None})

def main():
    lo,hi,_,categories=get_filter_options();cat="health_beauty" if "health_beauty" in categories else categories[0];period=(date(2018,1,1),date(2018,3,31))
    contexts={"full":FilterState(lo,hi),"date":FilterState(*period),"SP":FilterState(date(2018,1,1),date(2018,3,31),("SP",)),"category":FilterState(*period,(),(cat,)),"date_SP":FilterState(*period,("SP",)),"date_category":FilterState(*period,(),(cat,)),"date_SP_category":FilterState(*period,("SP",),(cat,))}
    for name,filters in contexts.items():validate(name,filters)
    f=contexts["date"];started=perf_counter();compare_periods(f);print("cached_period_seconds",round(perf_counter()-started,4))
if __name__=="__main__":main()
