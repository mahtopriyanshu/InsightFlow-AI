"""Advanced, grain-safe Product and Seller Intelligence analytics."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from streamlit_app.database.connection import query_dataframe
from streamlit_app.services.common import filtered_orders_cte
from streamlit_app.utils.filters import FilterState

MIN_CATEGORY_REVIEWS = 25
MIN_CATEGORY_ORDERS = 25
MIN_PRODUCT_ORDERS = 10
MIN_SELLER_ORDERS = 20
MIN_STATE_SELLERS = 5


def _category_expression() -> str:
    return "COALESCE(t.product_category_name_english, p.product_category_name)"


def _category_scope(filters: FilterState) -> tuple[str, tuple[str, ...]]:
    if not filters.categories: return "TRUE", ()
    placeholders=", ".join(["%s"]*len(filters.categories))
    return f"{_category_expression()} IN ({placeholders})", filters.categories


@st.cache_data(ttl=300, show_spinner=False)
def get_category_analytics(filters: FilterState) -> pd.DataFrame:
    cte, params = filtered_orders_cte(filters)
    category = _category_expression()
    scope,scope_params=_category_scope(filters)
    return query_dataframe(cte + f"""
      , item_metrics AS (
        SELECT {category} category, COUNT(DISTINCT p.product_id) products,
          COUNT(DISTINCT i.order_id) orders, COUNT(*) units,
          SUM(i.price) merchandise_revenue, AVG(i.price) average_item_price,
          SUM(i.freight_value) freight, AVG(i.freight_value) average_freight_item
        FROM filtered_orders f JOIN olist_analytics.order_items i USING(order_id)
        JOIN olist_analytics.products p USING(product_id)
        LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name)
        WHERE {scope} GROUP BY 1), review_rows AS (
        SELECT DISTINCT r.review_id, {category} category, r.review_score
        FROM filtered_orders f JOIN olist_analytics.order_reviews r USING(order_id)
        JOIN olist_analytics.order_items i USING(order_id)
        JOIN olist_analytics.products p USING(product_id)
        LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name)
        WHERE {scope}),
      review_metrics AS (SELECT category, COUNT(*) reviews, AVG(review_score) average_review_score
        FROM review_rows GROUP BY category), delivery_rows AS (
        SELECT DISTINCT f.order_id, {category} category, f.order_status,
          d.delivery_performance, d.actual_delivery_days
        FROM filtered_orders f JOIN delivery_metrics d USING(order_id)
        JOIN olist_analytics.order_items i USING(order_id)
        JOIN olist_analytics.products p USING(product_id)
        LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name)
        WHERE {scope}),
      delivery_agg AS (SELECT category,
        COUNT(*) FILTER(WHERE order_status='delivered') delivered_orders,
        COUNT(*) FILTER(WHERE delivery_performance<>'not_delivered') eligible_deliveries,
        100.0*COUNT(*) FILTER(WHERE delivery_performance='late') /
          NULLIF(COUNT(*) FILTER(WHERE delivery_performance<>'not_delivered'),0) late_rate,
        AVG(actual_delivery_days) average_delivery_days FROM delivery_rows GROUP BY category)
      SELECT i.*, 100.0*i.freight/NULLIF(i.merchandise_revenue,0) freight_ratio,
        r.reviews, r.average_review_score, d.delivered_orders, d.eligible_deliveries,
        d.late_rate, d.average_delivery_days
      FROM item_metrics i LEFT JOIN review_metrics r USING(category)
      LEFT JOIN delivery_agg d USING(category)
      ORDER BY merchandise_revenue DESC
    """, (*params,*scope_params,*scope_params,*scope_params))


@st.cache_data(ttl=300, show_spinner=False)
def get_product_analytics(filters: FilterState) -> pd.DataFrame:
    cte, params = filtered_orders_cte(filters)
    category = _category_expression()
    scope,scope_params=_category_scope(filters)
    return query_dataframe(cte + f"""
      , item_metrics AS (SELECT i.product_id, {category} category,
        COUNT(DISTINCT i.order_id) orders, COUNT(*) units,
        SUM(i.price) merchandise_revenue, AVG(i.price) average_item_price,
        SUM(i.freight_value) freight
        FROM filtered_orders f JOIN olist_analytics.order_items i USING(order_id)
        JOIN olist_analytics.products p USING(product_id)
        LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name)
        WHERE {scope} GROUP BY i.product_id, 2), review_rows AS (
        SELECT DISTINCT r.review_id, i.product_id, r.review_score
        FROM filtered_orders f JOIN olist_analytics.order_reviews r USING(order_id)
        JOIN olist_analytics.order_items i USING(order_id)
        JOIN olist_analytics.products p USING(product_id)
        LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name)
        WHERE {scope}),
      reviews AS (SELECT product_id, COUNT(*) reviews, AVG(review_score) average_review_score
        FROM review_rows GROUP BY product_id), delivery_rows AS (
        SELECT DISTINCT f.order_id, i.product_id, d.delivery_performance, d.actual_delivery_days
        FROM filtered_orders f JOIN delivery_metrics d USING(order_id)
        JOIN olist_analytics.order_items i USING(order_id)
        JOIN olist_analytics.products p USING(product_id)
        LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name)
        WHERE {scope}),
      delivery AS (SELECT product_id,
        COUNT(*) FILTER(WHERE delivery_performance<>'not_delivered') eligible_deliveries,
        100.0*COUNT(*) FILTER(WHERE delivery_performance='late') /
          NULLIF(COUNT(*) FILTER(WHERE delivery_performance<>'not_delivered'),0) late_rate,
        AVG(actual_delivery_days) average_delivery_days FROM delivery_rows GROUP BY product_id)
      SELECT i.*,100.0*i.freight/NULLIF(i.merchandise_revenue,0) freight_ratio,
        r.reviews,r.average_review_score,d.eligible_deliveries,d.late_rate,d.average_delivery_days
      FROM item_metrics i LEFT JOIN reviews r USING(product_id)
      LEFT JOIN delivery d USING(product_id) ORDER BY merchandise_revenue DESC
    """, (*params,*scope_params,*scope_params,*scope_params))


@st.cache_data(ttl=300, show_spinner=False)
def get_seller_analytics(filters: FilterState) -> pd.DataFrame:
    cte, params = filtered_orders_cte(filters)
    scope,scope_params=_category_scope(filters)
    return query_dataframe(cte + f"""
      , item_metrics AS (SELECT i.seller_id,s.seller_state state,s.seller_city city,
        COUNT(DISTINCT i.order_id) orders,COUNT(*) units,SUM(i.price) merchandise_revenue,
        AVG(i.price) average_item_value,SUM(i.freight_value) freight
        FROM filtered_orders f JOIN olist_analytics.order_items i USING(order_id)
        JOIN olist_analytics.sellers s USING(seller_id)
        JOIN olist_analytics.products p USING(product_id)
        LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name)
        WHERE {scope} GROUP BY 1,2,3), review_rows AS (
        SELECT DISTINCT r.review_id,i.seller_id,r.review_score
        FROM filtered_orders f JOIN olist_analytics.order_reviews r USING(order_id)
        JOIN olist_analytics.order_items i USING(order_id)
        JOIN olist_analytics.products p USING(product_id)
        LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name)
        WHERE {scope}),
      reviews AS (SELECT seller_id,COUNT(*) reviews,AVG(review_score) average_review_score
        FROM review_rows GROUP BY seller_id), delivery_rows AS (
        SELECT DISTINCT f.order_id,i.seller_id,f.order_status,d.delivery_performance,d.actual_delivery_days
        FROM filtered_orders f JOIN delivery_metrics d USING(order_id)
        JOIN olist_analytics.order_items i USING(order_id)
        JOIN olist_analytics.products p USING(product_id)
        LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name)
        WHERE {scope}),
      delivery AS (SELECT seller_id,
        COUNT(*) FILTER(WHERE order_status='delivered') delivered_orders,
        COUNT(*) FILTER(WHERE delivery_performance<>'not_delivered') eligible_deliveries,
        100.0*COUNT(*) FILTER(WHERE delivery_performance='late') /
          NULLIF(COUNT(*) FILTER(WHERE delivery_performance<>'not_delivered'),0) late_rate,
        AVG(actual_delivery_days) average_delivery_days FROM delivery_rows GROUP BY seller_id)
      SELECT i.*,100.0*i.freight/NULLIF(i.merchandise_revenue,0) freight_ratio,
        r.reviews,r.average_review_score,d.delivered_orders,d.eligible_deliveries,
        d.late_rate,d.average_delivery_days,
        100.0*d.delivered_orders/NULLIF(i.orders,0) delivery_rate
      FROM item_metrics i LEFT JOIN reviews r USING(seller_id)
      LEFT JOIN delivery d USING(seller_id) ORDER BY merchandise_revenue DESC
    """, (*params,*scope_params,*scope_params,*scope_params))


@st.cache_data(ttl=300, show_spinner=False)
def get_category_seller_concentration(filters: FilterState) -> pd.DataFrame:
    cte, params = filtered_orders_cte(filters)
    category = _category_expression()
    scope,scope_params=_category_scope(filters)
    return query_dataframe(cte + f"""
      , seller_category AS (SELECT {category} category,i.seller_id,SUM(i.price) revenue
        FROM filtered_orders f JOIN olist_analytics.order_items i USING(order_id)
        JOIN olist_analytics.products p USING(product_id)
        LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name)
        WHERE {scope} GROUP BY 1,2), ranked AS (SELECT *,SUM(revenue) OVER(PARTITION BY category) category_revenue,
        ROW_NUMBER() OVER(PARTITION BY category ORDER BY revenue DESC,seller_id) rank
        FROM seller_category)
      SELECT category,COUNT(*) sellers,MAX(category_revenue) category_revenue,
        100.0*MAX(revenue) FILTER(WHERE rank=1)/NULLIF(MAX(category_revenue),0) top_seller_share,
        100.0*SUM(revenue) FILTER(WHERE rank<=5)/NULLIF(MAX(category_revenue),0) top_5_seller_share
      FROM ranked GROUP BY category ORDER BY category_revenue DESC
    """, (*params,*scope_params))


def concentration(frame: pd.DataFrame, value: str) -> tuple[pd.DataFrame, dict[str, float]]:
    """Exact Pareto metrics with a browser-safe cumulative curve."""
    if frame.empty: return pd.DataFrame(), {}
    ranked = frame.sort_values(value, ascending=False).reset_index(drop=True).copy()
    values = pd.to_numeric(ranked[value], errors="coerce").fillna(0).clip(lower=0)
    total = float(values.sum())
    ranked["entity_share"] = 100*np.arange(1,len(ranked)+1)/len(ranked)
    ranked["revenue_share"] = 100*values.cumsum()/total if total else 0
    hit = ranked.loc[ranked.revenue_share>=80,"entity_share"]
    top10n=max(1,int(np.ceil(len(ranked)*.1)))
    metrics={"entities_for_80":float(hit.iloc[0]) if len(hit) else 100.0,
      "top_10pct_share":100*float(values.iloc[:top10n].sum())/total if total else 0,
      "top_5_share":100*float(values.iloc[:5].sum())/total if total else 0,
      "top_10_share":100*float(values.iloc[:10].sum())/total if total else 0}
    points=ranked.iloc[np.unique(np.linspace(0,len(ranked)-1,min(1000,len(ranked))).astype(int))]
    return points[["entity_share","revenue_share"]].rename(columns={"entity_share":"customer_share"}),metrics


def category_signals(categories: pd.DataFrame) -> pd.DataFrame:
    q=categories.loc[(categories.orders>=MIN_CATEGORY_ORDERS)&(categories.reviews>=MIN_CATEGORY_REVIEWS)].copy()
    if q.empty:return q
    numeric=["orders","reviews","merchandise_revenue","average_review_score","freight_ratio","late_rate"]
    q[numeric]=q[numeric].apply(pd.to_numeric,errors="coerce")
    revenue_median=float(q.merchandise_revenue.median()); review_benchmark=float(np.average(q.average_review_score,weights=q.reviews))
    freight_median=float(q.freight_ratio.median()); late_median=float(q.late_rate.median())
    q["signal"]="Balanced"
    q.loc[(q.merchandise_revenue>=revenue_median)&(q.average_review_score<review_benchmark),"signal"]="Experience Risk"
    q.loc[(q.orders>=q.orders.median())&(q.late_rate>late_median),"signal"]="Fulfillment Watch"
    q.loc[q.freight_ratio>freight_median*1.5,"signal"]="Freight Watch"
    q.loc[(q.average_review_score>=review_benchmark)&(q.orders>=q.orders.median())&(q.merchandise_revenue<revenue_median),"signal"]="Opportunity Signal"
    q.attrs.update(revenue_median=revenue_median,review_benchmark=review_benchmark,freight_median=freight_median,late_median=late_median)
    return q


def seller_signals(sellers: pd.DataFrame) -> pd.DataFrame:
    q=sellers.loc[sellers.orders>=MIN_SELLER_ORDERS].copy()
    if q.empty:return q
    numeric=["orders","merchandise_revenue","late_rate"]
    q[numeric]=q[numeric].apply(pd.to_numeric,errors="coerce")
    revenue_median=float(q.merchandise_revenue.median()); late_median=float(q.late_rate.median())
    q["signal"]="Balanced"
    q.loc[(q.merchandise_revenue>=revenue_median)&(q.late_rate>late_median),"signal"]="Fulfillment Watch"
    q.loc[(q.merchandise_revenue>=q.merchandise_revenue.quantile(.75))&(q.late_rate>late_median),"signal"]="Operational Risk Signal"
    q.attrs.update(revenue_median=revenue_median,late_median=late_median)
    return q
