"""Seven-scope M17 acceptance gate and performance check."""
from datetime import date
from pathlib import Path
from time import perf_counter
import math,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from streamlit_app.health import build_health_report
from streamlit_app.services.common import get_filter_options
from streamlit_app.utils.filters import FilterState
def check(name,filters):
    started=perf_counter();report=build_health_report(filters);elapsed=perf_counter()-started
    scores=[report.overall.score]+[d.score for d in report.dimensions if d.score is not None]
    assert all(math.isfinite(x) and 0<=x<=100 for x in scores)
    assert all(s.evidence and s.evidence.scope for s in report.risks+report.opportunities+report.recommendations)
    assert all(" caused " not in f" {s.message.lower()} " and " because of " not in s.message.lower() for s in report.risks+report.opportunities+report.recommendations)
    if filters.states:assert all("SP" in s.evidence.scope for s in report.risks+report.opportunities+report.recommendations)
    if filters.categories:assert all(filters.categories[0] in s.evidence.scope for s in report.risks+report.opportunities+report.recommendations)
    assert all(any(r.metric==x.metric and r.evidence==x.evidence for r in report.risks) for x in report.recommendations)
    print(name,{"overall":round(report.overall.score,2),"dimensions":{d.name:round(d.score,2) if d.score is not None else None for d in report.dimensions},"risks":len(report.risks),"opportunities":len(report.opportunities),"seconds":round(elapsed,3)})
def main():
    lo,hi,_,cats=get_filter_options();cat="health_beauty" if "health_beauty" in cats else cats[0];p=(date(2018,1,1),date(2018,3,31))
    contexts={"full":FilterState(lo,hi),"date":FilterState(*p),"SP":FilterState(lo,hi,("SP",)),"category":FilterState(lo,hi,(),(cat,)),"date_SP":FilterState(*p,("SP",)),"date_category":FilterState(*p,(),(cat,)),"date_SP_category":FilterState(*p,("SP",),(cat,))}
    for name,f in contexts.items():check(name,f)
    started=perf_counter();build_health_report(contexts["full"]);print("cached_seconds",round(perf_counter()-started,4))
if __name__=="__main__":main()
