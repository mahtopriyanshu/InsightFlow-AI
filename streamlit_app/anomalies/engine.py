"""Orchestrate metric, category, and seller anomaly detection."""
import pandas as pd
from streamlit_app.anomalies.baselines import complete_months
from streamlit_app.anomalies.config import MAX_EXECUTIVE_ALERTS,MIN_CATEGORY_MONTHLY_ORDERS,MIN_MONTHLY_ORDERS,MIN_MONTHLY_REVIEWS,MIN_SELLER_MONTHLY_ORDERS
from streamlit_app.anomalies.detectors import detect_series
from streamlit_app.services.anomaly_history import get_business_history,get_category_history,get_complete_order_months,get_seller_history

def _in_analysis_period(alerts,filters):
    start=pd.Timestamp(filters.start_date).to_period("M");end=pd.Timestamp(filters.end_date).to_period("M")
    return [a for a in alerts if start<=pd.Timestamp(a.period).to_period("M")<=end]

def build_alerts(filters,*,include_business=True,category_labels:tuple[str,...]=(),seller_labels:tuple[str,...]=(),limit:int=MAX_EXECUTIVE_ALERTS):
    """Return prioritized filter-aware alerts using pre-scope historical context."""
    alerts=[];complete_periods=set()
    if include_business:
        business=complete_months(get_business_history(filters));complete_periods=set(pd.to_datetime(business.month).dt.to_period("M"))
    elif category_labels or seller_labels:
        complete=complete_months(get_complete_order_months(filters));complete_periods=set(pd.to_datetime(complete.month).dt.to_period("M"))
    if include_business:
        for metric,sample_col,min_sample in (
          ("revenue","orders",MIN_MONTHLY_ORDERS),("orders","orders",MIN_MONTHLY_ORDERS),("average_order_value","orders",MIN_MONTHLY_ORDERS),
          ("unique_customers","orders",MIN_MONTHLY_ORDERS),("repeat_rate","orders",MIN_MONTHLY_ORDERS),("revenue_per_customer","orders",MIN_MONTHLY_ORDERS),
          ("delivery_rate","eligible_deliveries",MIN_MONTHLY_ORDERS),("late_rate","eligible_deliveries",MIN_MONTHLY_ORDERS),("average_delivery_days","eligible_deliveries",MIN_MONTHLY_ORDERS),
          ("average_review_score","reviews",MIN_MONTHLY_REVIEWS),("negative_review_rate","reviews",MIN_MONTHLY_REVIEWS),("one_star_rate","reviews",MIN_MONTHLY_REVIEWS),("five_star_rate","reviews",MIN_MONTHLY_REVIEWS)):
            alerts.extend(detect_series(business,metric,filters,sample_column=sample_col,min_sample=min_sample))
    if category_labels:
        history=get_category_history(filters,category_labels);history=history.loc[pd.to_datetime(history.month).dt.to_period("M").isin(complete_periods)]
        for label,group in history.groupby("entity_label"):
            entity_alerts=[]
            for metric in ("merchandise_revenue","orders"):
                entity_alerts.extend(detect_series(group.reset_index(drop=True),metric,filters,entity_type="category",entity_label=str(label),sample_column="sample_size",min_sample=MIN_CATEGORY_MONTHLY_ORDERS))
            entity_alerts.extend(detect_series(group.reset_index(drop=True),"average_review_score",filters,entity_type="category",entity_label=str(label),sample_column="reviews",min_sample=MIN_MONTHLY_REVIEWS))
            bad_periods={a.period for a in entity_alerts if a.metric=="average_review_score" and a.category!="opportunity"}
            alerts.extend(a for a in entity_alerts if not (a.category=="opportunity" and a.metric in {"orders","merchandise_revenue"} and a.period in bad_periods))
    if seller_labels:
        history=get_seller_history(filters,seller_labels);history=history.loc[pd.to_datetime(history.month).dt.to_period("M").isin(complete_periods)]
        for label,group in history.groupby("entity_label"):
            entity_alerts=[]
            for metric in ("merchandise_revenue","orders","late_rate"):
                entity_alerts.extend(detect_series(group.reset_index(drop=True),metric,filters,entity_type="seller",entity_label=str(label),sample_column="sample_size",min_sample=MIN_SELLER_MONTHLY_ORDERS))
            bad_periods={a.period for a in entity_alerts if a.metric=="late_rate" and a.category!="opportunity"}
            alerts.extend(a for a in entity_alerts if not (a.category=="opportunity" and a.metric in {"orders","merchandise_revenue"} and a.period in bad_periods))
    alerts=_in_analysis_period(alerts,filters)
    return sorted(alerts,key=lambda item:(pd.Timestamp(item.period),item.priority),reverse=True)[:limit]
