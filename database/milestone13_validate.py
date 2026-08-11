"""Live M13 filter, reconciliation, concentration, signal, and timing checks."""
from datetime import date
from pathlib import Path
from time import perf_counter
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from streamlit_app.insights import product_pro_insights,seller_pro_insights
from streamlit_app.services.common import get_filter_options
from streamlit_app.services.portfolio import *
from streamlit_app.utils.filters import FilterState


def validate(name,filters):
    started=perf_counter();cats=get_category_analytics(filters);cat_s=perf_counter()-started
    started=perf_counter();products=get_product_analytics(filters);prod_s=perf_counter()-started
    started=perf_counter();sellers=get_seller_analytics(filters);seller_s=perf_counter()-started
    started=perf_counter();cross=get_category_seller_concentration(filters);cross_s=perf_counter()-started
    totals=[float(cats.merchandise_revenue.sum()),float(products.merchandise_revenue.sum()),float(sellers.merchandise_revenue.sum()),float(cross.category_revenue.sum())]
    assert max(totals)-min(totals)<.01
    assert int(cats.units.sum())==int(products.units.sum())==int(sellers.units.sum())
    cat_curve,cat_c=concentration(cats,"merchandise_revenue");prod_curve,prod_c=concentration(products,"merchandise_revenue");seller_curve,seller_c=concentration(sellers,"merchandise_revenue")
    for curve in (cat_curve,prod_curve,seller_curve):
        assert curve.revenue_share.is_monotonic_increasing
    cs=category_signals(cats);ss=seller_signals(sellers)
    pi=product_pro_insights(filters,cats,cat_c,cs);si=seller_pro_insights(filters,sellers,seller_c,ss)
    assert all(x.evidence and x.scope for x in pi+si)
    if filters.states:assert all("SP" in x.scope for x in pi+si)
    if filters.categories:assert all(filters.categories[0] in x.scope for x in pi+si)
    print(name,{"revenue":round(totals[0],2),"categories":len(cats),"products":len(products),"sellers":len(sellers),"category_80":round(cat_c["entities_for_80"],2),"product_80":round(prod_c["entities_for_80"],2),"seller_80":round(seller_c["entities_for_80"],2),"cat_signals":cs.signal.value_counts().to_dict(),"seller_signals":ss.signal.value_counts().to_dict(),"seconds":{"category":round(cat_s,3),"product":round(prod_s,3),"seller":round(seller_s,3),"cross":round(cross_s,3)}})


def main():
    lo,hi,_,categories=get_filter_options();cat="health_beauty" if "health_beauty" in categories else categories[0];period=(date(2018,1,1),date(2018,6,30))
    contexts={"full":FilterState(lo,hi),"date":FilterState(*period),"SP":FilterState(lo,hi,("SP",)),"category":FilterState(lo,hi,(),(cat,)),"date_SP":FilterState(*period,("SP",)),"date_category":FilterState(*period,(),(cat,)),"date_SP_category":FilterState(*period,("SP",),(cat,))}
    for name,filters in contexts.items():validate(name,filters)


if __name__=="__main__":main()
