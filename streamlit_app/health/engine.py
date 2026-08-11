"""Filter-aware deterministic health scoring and recommendation center."""
import numpy as np
import pandas as pd
from streamlit_app.anomalies import build_alerts
from streamlit_app.anomalies.baselines import complete_months
from streamlit_app.health.config import band
from streamlit_app.health.models import HealthComponent,HealthDimension,HealthEvidence,HealthReport,HealthSignal
from streamlit_app.insights.comparisons import period_label,scope_label
from streamlit_app.services.anomaly_history import get_business_history
from streamlit_app.services.comparisons import compare_periods
from streamlit_app.services.customers import get_customer_metrics
from streamlit_app.services.operations import get_delivery_metrics,get_review_metrics,get_review_distribution
from streamlit_app.services.overview import get_kpis
from streamlit_app.services.portfolio import category_signals,get_category_analytics,get_seller_analytics,seller_signals
from streamlit_app.services.rfm import get_rfm_customers,get_segment_summary
from streamlit_app.utils.formatting import currency,number,percentage

def _score(observed,benchmark,tolerance,higher=True):
    observed=float(observed);benchmark=float(benchmark);tolerance=max(float(tolerance),1e-9)
    direction=1 if higher else -1
    return float(np.clip(50+25*direction*(observed-benchmark)/tolerance,0,100))
def _component(name,metric,observed,benchmark,tolerance,weight,unit,reason,higher=True):
    score=_score(observed,benchmark,tolerance,higher);return HealthComponent(name,metric,float(observed),float(benchmark),score,weight,score*weight,unit,reason)
def _dimension(name,components):
    available=[c for c in components if c.available]
    if not available:return HealthDimension(name,None,"Unavailable",())
    total=sum(c.weight for c in available);score=sum(c.score*c.weight for c in available)/total
    normalized=tuple(HealthComponent(c.name,c.metric,c.observed,c.benchmark,c.score,c.weight/total,c.score*c.weight/total,c.unit,c.reason,c.available) for c in available)
    return HealthDimension(name,score,band(score),normalized)
def _median_scale(history,column,minimum):
    values=pd.to_numeric(history[column],errors="coerce").dropna();median=float(values.median());mad=float((values-median).abs().median())
    return median,max(1.4826*mad,minimum)
def _fmt(value,unit):
    if unit=="currency":return currency(value)
    if unit=="percentage":return percentage(value)
    if unit=="days":return f"{number(value,1)} days"
    if unit=="score":return f"{number(value,2)} / 5"
    return number(value)

def build_health_report(filters):
    k=get_kpis(filters).iloc[0];c=get_customer_metrics(filters).iloc[0];d=get_delivery_metrics(filters).iloc[0];r=get_review_metrics(filters).iloc[0]
    history=complete_months(get_business_history(filters));comparison=compare_periods(filters)
    rev=[]
    if comparison.available:
        by={m.key:m for m in comparison.metrics}
        for name,key,weight in (("Revenue movement","revenue",.45),("Order movement","orders",.35),("AOV movement","aov",.20)):
            m=by[key]
            if m.available:rev.append(_component(name,key,m.left_value,m.right_value,max(abs(m.right_value)*.10,1),weight,m.unit,"Valid previous equal-duration period",True))
    if not rev and not history.empty:
        median,tol=_median_scale(history,"average_order_value",10);rev.append(_component("AOV vs historical norm","aov",k.average_order_value,median,tol,1,"currency","Same-scope completed-month median",True))
    revenue=_dimension("Revenue Health",rev)
    cust=[]
    for name,col,observed,weight in (("Revenue per customer","revenue_per_customer",c.revenue_per_customer,.55),("Repeat customer rate","repeat_rate",c.repeat_rate,.45)):
        median,tol=_median_scale(history,col,10 if col=="revenue_per_customer" else 1)
        cust.append(_component(name,col,observed,median,tol,weight,"currency" if col=="revenue_per_customer" else "percentage","Same-scope completed-month median",True))
    customer=_dimension("Customer Health",cust)
    fulfillment=[]
    for name,col,observed,weight,higher,minimum,unit in (("Delivery rate","delivery_rate",d.delivery_rate,.35,True,3,"percentage"),("Late-delivery rate","late_rate",d.late_rate,.40,False,3,"percentage"),("Average delivery days","average_delivery_days",d.average_delivery_days,.25,False,1.5,"days")):
        median,tol=_median_scale(history,col,minimum);fulfillment.append(_component(name,col,observed,median,tol,weight,unit,"Same-scope completed-month median",higher))
    fulfillment=_dimension("Fulfillment Health",fulfillment)
    dist=get_review_distribution(filters);total=max(float(dist.reviews.sum()),1);five=100*float(dist.loc[dist.review_score.eq(5),"reviews"].sum())/total
    satisfaction=[]
    for name,col,observed,weight,higher,minimum,unit in (("Average review score","average_review_score",r.average_review_score,.45,True,.25,"score"),("Negative-review rate","negative_review_rate",r.negative_review_rate,.35,False,3,"percentage"),("Five-star share","five_star_rate",five,.20,True,5,"percentage")):
        median,tol=_median_scale(history,col,minimum);satisfaction.append(_component(name,col,observed,median,tol,weight,unit,"Same-scope completed-month median",higher))
    satisfaction=_dimension("Satisfaction Health",satisfaction)
    dimensions=(revenue,customer,fulfillment,satisfaction);valid=[x for x in dimensions if x.score is not None];overall_score=sum(x.score for x in valid)/len(valid)
    overall=HealthDimension("Overall Business Health",overall_score,band(overall_score),())
    scope=scope_label(filters);period=period_label(filters);risks=[];opportunities=[]
    for alert in build_alerts(filters):
        evidence=HealthEvidence(alert.evidence.observed,alert.evidence.baseline,alert.period,alert.evidence.sample_size,scope,"M14 Anomaly Detection",alert.message)
        signal=HealthSignal(alert.title,alert.message,"opportunity" if alert.category=="opportunity" else "risk",alert.severity,alert.metric,alert.entity_label,evidence,alert.priority)
        (opportunities if alert.category=="opportunity" else risks).append(signal)
    profiles=get_rfm_customers(filters);segments=get_segment_summary(profiles)
    at=segments.loc[segments.segment.astype(str).eq("At Risk")]
    if not at.empty:
        row=at.iloc[0];risks.append(HealthSignal("Historical customer-value watch",f"At-Risk RFM customers represent {float(row.customer_share):.1f}% of customers and {float(row.revenue_share):.1f}% of selected revenue.","risk","warning","at_risk_share","At Risk",HealthEvidence(percentage(row.revenue_share),percentage(row.customer_share),period,int(row.customers),scope,"M12 RFM","Historical behavior label; not churn prediction"),88))
    champions=segments.loc[segments.segment.astype(str).eq("Champions")]
    if not champions.empty:
        row=champions.iloc[0];opportunities.append(HealthSignal("Champion customer strength",f"Champions contribute {float(row.revenue_share):.1f}% of selected revenue.","opportunity","positive","champion_revenue_share","Champions",HealthEvidence(percentage(row.revenue_share),percentage(row.customer_share),period,int(row.customers),scope,"M12 RFM","High historical value signal"),76))
    categories=get_category_analytics(filters);cs=category_signals(categories)
    for _,row in cs.loc[cs.signal.isin(["Experience Risk","Fulfillment Watch"])].sort_values("merchandise_revenue",ascending=False).head(2).iterrows():
        risks.append(HealthSignal(str(row.signal),f"{row.category} combines meaningful commercial exposure with {str(row.signal).lower()} evidence.","risk","warning",str(row.signal),str(row.category),HealthEvidence(currency(row.merchandise_revenue),percentage(row.late_rate),period,int(row.orders),scope,"M13 Product Intelligence","Qualifying benchmark-relative signal"),72))
    for _,row in cs.loc[cs.signal.eq("Opportunity Signal")].head(2).iterrows():
        opportunities.append(HealthSignal("Category opportunity signal",f"{row.category} combines above-reference reviews with meaningful demand.","opportunity","positive","category_opportunity",str(row.category),HealthEvidence(currency(row.merchandise_revenue),number(row.average_review_score,2),period,int(row.orders),scope,"M13 Product Intelligence","Signal only; not a recommendation"),68))
    recommendations=[]
    for risk in sorted(risks,key=lambda x:x.priority,reverse=True)[:5]:
        verb="Investigate" if "delivery" in risk.metric.lower() or "fulfillment" in risk.metric.lower() else "Review"
        recommendations.append(HealthSignal(f"{verb} {risk.title.lower()}",f"{verb} the evidence behind {risk.title.lower()} before making an operational decision.","recommendation","informational",risk.metric,risk.entity,risk.evidence,risk.priority-5))
    return HealthReport(overall,dimensions,tuple(sorted(risks,key=lambda x:x.priority,reverse=True)[:5]),tuple(sorted(opportunities,key=lambda x:x.priority,reverse=True)[:5]),tuple(recommendations))
