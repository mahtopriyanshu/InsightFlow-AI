"""Deterministic contribution and association analysis for comparable periods."""
import pandas as pd
from streamlit_app.insights.comparisons import previous_comparable_period,scope_label
from streamlit_app.root_cause.decomposition import revenue_decomposition
from streamlit_app.root_cause.models import Driver,DriverAnalysis,DriverEvidence
from streamlit_app.services.common import get_filter_options
from streamlit_app.services.comparisons import period_snapshot
from streamlit_app.services.overview import get_category_performance,get_payment_methods,get_state_performance
from streamlit_app.services.portfolio import get_seller_analytics
from streamlit_app.services.operations import get_delivery_by_state,get_review_distribution,get_delivery_review_relationship
from streamlit_app.services.customers import get_customer_locations,get_customer_metrics

def _periods(filters,previous):return f"{filters.start_date:%d %b %Y} – {filters.end_date:%d %b %Y}",f"{previous.start_date:%d %b %Y} – {previous.end_date:%d %b %Y}"
def _drivers(kpi,dimension,current,previous,key,value,total_change,filters,previous_filters,definition,limit=5,min_sample_key=None,min_sample=0):
    total_change=float(total_change)
    merged=current[[key,value]+([min_sample_key] if min_sample_key and min_sample_key not in (key,value) else [])].merge(previous[[key,value]],on=key,how="outer",suffixes=("_current","_previous")).fillna(0)
    if min_sample_key and min_sample_key in merged:merged=merged.loc[merged[min_sample_key]>=min_sample]
    merged["change"]=pd.to_numeric(merged[f"{value}_current"],errors="coerce")-pd.to_numeric(merged[f"{value}_previous"],errors="coerce")
    merged=merged.loc[merged.change.ne(0)].sort_values("change",key=lambda x:x.abs(),ascending=False).head(limit)
    cp,pp=_periods(filters,previous_filters);result=[]
    for _,row in merged.iterrows():
        relative=None if abs(total_change)<1e-9 else 100*float(row.change)/total_change
        direction="positive" if row.change>0 else "negative"
        wording=f"{row[key]} recorded the largest observed {direction} {dimension.lower()} movement of {abs(float(row.change)):,.2f}."
        result.append(Driver(kpi,dimension,str(row[key]),float(row[f"{value}_current"]),float(row[f"{value}_previous"]),float(row.change),relative,direction,DriverEvidence(cp,pp,definition,scope_label(filters)),wording))
    return result

def analyze_change(filters,kpi="Revenue"):
    earliest,*_=get_filter_options();comparison=previous_comparable_period(filters,earliest)
    if not comparison.available:return DriverAnalysis(kpi,0,0,0,(),scope=scope_label(filters),available=False,reason="Comparable period unavailable")
    previous=comparison.previous;current,cs=period_snapshot(filters);old,ps=period_snapshot(previous);cp,pp=_periods(filters,previous)
    drivers=[];narrative=[]
    if kpi=="Revenue":
        dec=revenue_decomposition(current["orders"],current["aov"],old["orders"],old["aov"]);total=current["revenue"]-old["revenue"]
        for dimension,key in (("Order volume","volume"),("Average order value","aov")):
            value=dec[key];drivers.append(Driver("Payment Revenue",dimension,dimension,current["revenue"],old["revenue"],value,None,"positive" if value>0 else "negative",DriverEvidence(cp,pp,"Symmetric decomposition of payment revenue = orders × AOV",scope_label(filters),cs),f"{dimension} contributed {value:+,.2f} to the observed payment-revenue movement."))
        states_now=get_state_performance(filters);states_old=get_state_performance(previous)
        drivers+=_drivers("Payment Revenue","Destination state",states_now,states_old,"state","revenue",total,filters,previous,"Payment revenue by customer destination state")
        cats_now=get_category_performance(filters,100);cats_old=get_category_performance(previous,100)
        drivers+=_drivers("Merchandise Revenue","Category exposure",cats_now,cats_old,"category","revenue",float(cats_now.revenue.sum())-float(cats_old.revenue.sum()),filters,previous,"Order-item merchandise revenue; separate from payment revenue")
        sellers_now=get_seller_analytics(filters);sellers_old=get_seller_analytics(previous)
        drivers+=_drivers("Merchandise Revenue","Seller exposure",sellers_now,sellers_old,"seller_id","merchandise_revenue",float(sellers_now.merchandise_revenue.sum())-float(sellers_old.merchandise_revenue.sum()),filters,previous,"Seller order-item merchandise exposure",limit=3)
        narrative=(f"Payment revenue changed by {total:+,.2f}.","Order-volume and AOV contributions reconcile exactly; category and seller sections use explicitly separate merchandise revenue.")
        return DriverAnalysis("Payment Revenue",current["revenue"],old["revenue"],total,tuple(drivers),narrative,scope_label(filters))
    if kpi=="Orders":
        total=current["orders"]-old["orders"];cats_now=get_category_performance(filters,100);cats_old=get_category_performance(previous,100);states_now=get_state_performance(filters);states_old=get_state_performance(previous)
        drivers+=_drivers("Orders","Category exposure",cats_now,cats_old,"category","orders",total,filters,previous,"Distinct orders represented by category; categories can overlap")
        drivers+=_drivers("Orders","Destination state",states_now,states_old,"state","orders",total,filters,previous,"Distinct orders by destination state")
        return DriverAnalysis("Orders",current["orders"],old["orders"],total,tuple(drivers),("Category order exposure can overlap when orders contain multiple categories.",),scope_label(filters))
    if kpi=="Delivery":
        total=current["late_rate"]-old["late_rate"];now=get_delivery_by_state(filters);before=get_delivery_by_state(previous)
        drivers+=_drivers("Late Delivery Rate","Destination state",now,before,"state","late_rate",total,filters,previous,"Late rate by customer destination state",min_sample_key="delivered_orders",min_sample=100)
        return DriverAnalysis("Late Delivery Rate",current["late_rate"],old["late_rate"],total,tuple(drivers),("State movements are observed concentrations, not causes.",),scope_label(filters))
    if kpi=="Reviews":
        total=current["review_score"]-old["review_score"];now=get_review_distribution(filters);before=get_review_distribution(previous)
        drivers+=_drivers("Review Score","Score distribution",now,before,"review_score","reviews",float(now.reviews.sum())-float(before.reviews.sum()),filters,previous,"Count of order reviews by score")
        rel=get_delivery_review_relationship(filters);late=rel.loc[rel.delivery_performance.eq("late")];ontime=rel.loc[rel.delivery_performance.eq("on_time_or_early")]
        if not late.empty and not ontime.empty:narrative.append(f"Late-delivered orders averaged {float(late.iloc[0].average_review_score):.2f} stars versus {float(ontime.iloc[0].average_review_score):.2f} for on-time/early orders; this is an association.")
        return DriverAnalysis("Average Review Score",current["review_score"],old["review_score"],total,tuple(drivers),tuple(narrative),scope_label(filters))
    total=current["unique_customers"]-old["unique_customers"];now=get_customer_locations(filters).groupby("state",as_index=False).customers.sum();before=get_customer_locations(previous).groupby("state",as_index=False).customers.sum()
    drivers+=_drivers("Unique Customers","Destination state",now,before,"state","customers",total,filters,previous,"Distinct customer_unique_id represented by state")
    return DriverAnalysis("Unique Customers",current["unique_customers"],old["unique_customers"],total,tuple(drivers),(f"Repeat-customer rate moved from {old['repeat_rate']:.2f}% to {current['repeat_rate']:.2f}%.","At Risk remains a historical RFM label, not predicted churn."),scope_label(filters))
