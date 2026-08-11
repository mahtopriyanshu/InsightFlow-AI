"""Cached historical series for deterministic anomaly detection."""
from datetime import date
import pandas as pd
import streamlit as st
from streamlit_app.database.connection import query_dataframe
from streamlit_app.services.common import filtered_orders_cte,get_filter_options
from streamlit_app.utils.filters import FilterState

def baseline_filters(filters:FilterState)->FilterState:
    start,_,_,_=get_filter_options();return FilterState(start,filters.end_date,filters.states,filters.categories)

@st.cache_data(ttl=300,show_spinner=False)
def get_complete_order_months(filters:FilterState)->pd.DataFrame:
    """Return scoped month boundaries without loading full business metrics."""
    history=baseline_filters(filters);cte,params=filtered_orders_cte(history)
    return query_dataframe(cte+"""
      SELECT date_trunc('month',order_purchase_timestamp)::date AS month,
        MIN(order_purchase_timestamp)::date first_day,
        MAX(order_purchase_timestamp)::date last_day
      FROM filtered_orders GROUP BY 1 ORDER BY 1
    """,params)

@st.cache_data(ttl=300,show_spinner=False)
def get_business_history(filters:FilterState)->pd.DataFrame:
    history=baseline_filters(filters);cte,params=filtered_orders_cte(history)
    return query_dataframe(cte+"""
      , commercial AS (SELECT date_trunc('month',f.order_purchase_timestamp)::date AS month,
        MIN(f.order_purchase_timestamp)::date first_day,MAX(f.order_purchase_timestamp)::date last_day,
        COUNT(*) orders,COUNT(DISTINCT f.customer_unique_id) unique_customers,
        SUM(COALESCE(v.payment_revenue,0)) revenue,AVG(COALESCE(v.payment_revenue,0)) average_order_value,
        100.0*COUNT(*) FILTER(WHERE f.order_status='delivered')/NULLIF(COUNT(*),0) delivery_rate
        FROM filtered_orders f LEFT JOIN order_revenue v USING(order_id) GROUP BY 1),
      customer_rows AS (SELECT date_trunc('month',f.order_purchase_timestamp)::date AS month,f.customer_unique_id,
        COUNT(DISTINCT f.order_id) orders,SUM(COALESCE(v.payment_revenue,0)) revenue
        FROM filtered_orders f LEFT JOIN order_revenue v USING(order_id) GROUP BY 1,2),
      customer_month AS (SELECT month,100.0*COUNT(*) FILTER(WHERE orders>1)/NULLIF(COUNT(*),0) repeat_rate,
        AVG(revenue) revenue_per_customer FROM customer_rows GROUP BY month),
      delivery AS (SELECT date_trunc('month',f.order_purchase_timestamp)::date AS month,
        COUNT(*) FILTER(WHERE d.delivery_performance<>'not_delivered') eligible_deliveries,
        100.0*COUNT(*) FILTER(WHERE d.delivery_performance='late')/NULLIF(COUNT(*) FILTER(WHERE d.delivery_performance<>'not_delivered'),0) late_rate,
        AVG(d.actual_delivery_days) average_delivery_days FROM filtered_orders f JOIN delivery_metrics d USING(order_id) GROUP BY 1),
      review AS (SELECT date_trunc('month',f.order_purchase_timestamp)::date AS month,COUNT(*) reviews,
        AVG(r.review_score) average_review_score,
        100.0*COUNT(*) FILTER(WHERE r.review_score<=2)/NULLIF(COUNT(*),0) negative_review_rate,
        100.0*COUNT(*) FILTER(WHERE r.review_score=1)/NULLIF(COUNT(*),0) one_star_rate,
        100.0*COUNT(*) FILTER(WHERE r.review_score=5)/NULLIF(COUNT(*),0) five_star_rate
        FROM filtered_orders f JOIN olist_analytics.order_reviews r USING(order_id) GROUP BY 1)
      SELECT c.*,cm.repeat_rate,cm.revenue_per_customer,d.eligible_deliveries,d.late_rate,d.average_delivery_days,
        r.reviews,r.average_review_score,r.negative_review_rate,r.one_star_rate,r.five_star_rate
      FROM commercial c LEFT JOIN customer_month cm USING(month) LEFT JOIN delivery d USING(month)
      LEFT JOIN review r USING(month) ORDER BY month
    """,params)

@st.cache_data(ttl=300,show_spinner=False)
def get_category_history(filters:FilterState,categories:tuple[str,...])->pd.DataFrame:
    if not categories:return pd.DataFrame()
    history=baseline_filters(filters);cte,params=filtered_orders_cte(history);holders=", ".join(["%s"]*len(categories))
    return query_dataframe(cte+f"""
      , item_history AS (SELECT date_trunc('month',f.order_purchase_timestamp)::date AS month,
        COALESCE(t.product_category_name_english,p.product_category_name) entity_label,
        COUNT(DISTINCT i.order_id) sample_size,COUNT(DISTINCT i.order_id) orders,SUM(i.price) merchandise_revenue
      FROM filtered_orders f JOIN olist_analytics.order_items i USING(order_id)
      JOIN olist_analytics.products p USING(product_id)
      LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name)
      WHERE COALESCE(t.product_category_name_english,p.product_category_name) IN ({holders})
      GROUP BY 1,2), review_rows AS (SELECT DISTINCT r.review_id,
        date_trunc('month',f.order_purchase_timestamp)::date AS month,
        COALESCE(t.product_category_name_english,p.product_category_name) entity_label,r.review_score
        FROM filtered_orders f JOIN olist_analytics.order_reviews r USING(order_id)
        JOIN olist_analytics.order_items i USING(order_id) JOIN olist_analytics.products p USING(product_id)
        LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name)
        WHERE COALESCE(t.product_category_name_english,p.product_category_name) IN ({holders})),
      review_history AS (SELECT month,entity_label,COUNT(*) reviews,AVG(review_score) average_review_score
        FROM review_rows GROUP BY 1,2)
      SELECT i.*,r.reviews,r.average_review_score FROM item_history i LEFT JOIN review_history r USING(month,entity_label)
      ORDER BY entity_label,month
    """,(*params,*categories,*categories))

@st.cache_data(ttl=300,show_spinner=False)
def get_seller_history(filters:FilterState,sellers:tuple[str,...])->pd.DataFrame:
    if not sellers:return pd.DataFrame()
    history=baseline_filters(filters);cte,params=filtered_orders_cte(history);holders=", ".join(["%s"]*len(sellers))
    return query_dataframe(cte+f"""
      , seller_month_orders AS (SELECT DISTINCT date_trunc('month',f.order_purchase_timestamp)::date AS month,
        i.seller_id entity_label,f.order_id,d.delivery_performance
        FROM filtered_orders f JOIN delivery_metrics d USING(order_id)
        JOIN olist_analytics.order_items i USING(order_id) WHERE i.seller_id IN ({holders})),
      economics AS (SELECT date_trunc('month',f.order_purchase_timestamp)::date AS month,i.seller_id entity_label,
        COUNT(DISTINCT i.order_id) orders,SUM(i.price) merchandise_revenue
        FROM filtered_orders f JOIN olist_analytics.order_items i USING(order_id)
        WHERE i.seller_id IN ({holders}) GROUP BY 1,2),
      delivery AS (SELECT month,entity_label,COUNT(*) FILTER(WHERE delivery_performance<>'not_delivered') sample_size,
        100.0*COUNT(*) FILTER(WHERE delivery_performance='late')/NULLIF(COUNT(*) FILTER(WHERE delivery_performance<>'not_delivered'),0) late_rate
        FROM seller_month_orders GROUP BY 1,2)
      SELECT e.*,d.sample_size,d.late_rate FROM economics e LEFT JOIN delivery d USING(month,entity_label) ORDER BY entity_label,month
    """,(*params,*sellers,*sellers))
