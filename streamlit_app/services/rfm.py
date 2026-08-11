"""Filter-aware, deterministic customer RFM analytics."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from streamlit_app.database.connection import query_dataframe
from streamlit_app.services.common import filtered_orders_cte
from streamlit_app.utils.filters import FilterState


SEGMENT_ORDER = [
    "Champions", "Loyal Customers", "Potential Loyalists",
    "Recent Customers", "Promising", "Needs Attention", "At Risk",
    "Hibernating",
]
SEGMENT_COLORS = {
    "Champions": "#6C4CF5", "Loyal Customers": "#3B82F6",
    "Potential Loyalists": "#14B8A6", "Recent Customers": "#22C55E",
    "Promising": "#06B6D4", "Needs Attention": "#F59E0B",
    "At Risk": "#EF4444", "Hibernating": "#64748B",
}


def percentile_score(series: pd.Series, *, lower_is_better: bool = False) -> pd.Series:
    """Return reproducible 1-5 scores; identical values always share a score."""
    numeric = pd.to_numeric(series, errors="coerce")
    percentile = numeric.rank(method="average", pct=True)
    score = np.ceil(percentile * 5).clip(1, 5).fillna(1).astype(int)
    return (6 - score) if lower_is_better else score


def frequency_score(series: pd.Series) -> pd.Series:
    """Score heavily tied Olist frequency using transparent order-count bands."""
    frequency = pd.to_numeric(series, errors="coerce").fillna(0)
    return pd.Series(np.select(
        [frequency >= 5, frequency == 4, frequency == 3, frequency == 2],
        [5, 4, 3, 2], default=1,
    ), index=series.index, dtype="int64")


def assign_segments(frame: pd.DataFrame) -> pd.Series:
    """Assign one mutually exclusive behavioral segment to every RFM profile."""
    r, f, m = frame["r_score"], frame["f_score"], frame["m_score"]
    return pd.Series(np.select(
        [
            (r >= 4) & (f >= 2) & (m >= 4),
            (f >= 3) & (m >= 3),
            (r >= 4) & (f >= 2),
            (r == 5) & (f == 1),
            (r >= 4) & (m >= 3),
            (r <= 2) & ((f >= 2) | (m >= 4)),
            (r <= 3) & ((f >= 2) | (m >= 3)),
        ],
        [
            "Champions", "Loyal Customers", "Potential Loyalists",
            "Recent Customers", "Promising", "At Risk",
            "Needs Attention",
        ],
        default="Hibernating",
    ), index=frame.index, dtype="object")


@st.cache_data(ttl=300, show_spinner=False)
def get_rfm_customers(filters: FilterState) -> pd.DataFrame:
    """Return one scored profile per customer_unique_id in the selected scope."""
    cte, params = filtered_orders_cte(filters)
    profiles = query_dataframe(cte + """
        , latest_location AS (
            SELECT DISTINCT ON (customer_unique_id)
                customer_unique_id, customer_state, customer_city
            FROM filtered_orders
            ORDER BY customer_unique_id, order_purchase_timestamp DESC, order_id DESC
        )
        SELECT f.customer_unique_id,
               MAX(f.order_purchase_timestamp) AS last_purchase,
               COUNT(DISTINCT f.order_id) AS frequency,
               SUM(COALESCE(v.payment_revenue, 0)) AS monetary,
               l.customer_state AS state,
               l.customer_city AS city
        FROM filtered_orders f
        LEFT JOIN order_revenue v ON v.order_id = f.order_id
        LEFT JOIN latest_location l ON l.customer_unique_id = f.customer_unique_id
        GROUP BY f.customer_unique_id, l.customer_state, l.customer_city
        ORDER BY f.customer_unique_id
    """, params)
    if profiles.empty:
        return profiles

    profiles["last_purchase"] = pd.to_datetime(profiles["last_purchase"])
    profiles["frequency"] = pd.to_numeric(profiles["frequency"], errors="coerce").fillna(0).astype(int)
    profiles["monetary"] = pd.to_numeric(profiles["monetary"], errors="coerce").fillna(0.0).astype(float)
    observed_end = profiles["last_purchase"].max().normalize()
    effective_end = min(pd.Timestamp(filters.end_date), observed_end)
    reference_date = effective_end + pd.Timedelta(days=1)
    profiles["recency_days"] = (reference_date - profiles["last_purchase"].dt.normalize()).dt.days.astype(int)
    profiles["reference_date"] = reference_date.date()
    profiles["r_score"] = percentile_score(profiles["recency_days"], lower_is_better=True)
    profiles["f_score"] = frequency_score(profiles["frequency"])
    profiles["m_score"] = percentile_score(profiles["monetary"])
    profiles["segment"] = assign_segments(profiles)
    return profiles


def get_segment_summary(profiles: pd.DataFrame) -> pd.DataFrame:
    """Aggregate exact customer and revenue contribution by segment."""
    columns = ["segment", "customers", "customer_share", "revenue", "revenue_share",
               "avg_revenue_per_customer", "avg_orders", "avg_recency_days",
               "avg_frequency", "avg_monetary"]
    if profiles.empty:
        return pd.DataFrame(columns=columns)
    summary = profiles.groupby("segment", observed=True, as_index=False).agg(
        customers=("customer_unique_id", "nunique"), revenue=("monetary", "sum"),
        avg_revenue_per_customer=("monetary", "mean"), avg_orders=("frequency", "mean"),
        avg_recency_days=("recency_days", "mean"), avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
    )
    summary["customer_share"] = 100 * summary["customers"] / summary["customers"].sum()
    total_revenue = summary["revenue"].sum()
    summary["revenue_share"] = np.where(total_revenue > 0, 100 * summary["revenue"] / total_revenue, 0)
    summary["segment"] = pd.Categorical(summary["segment"], SEGMENT_ORDER, ordered=True)
    return summary.sort_values("segment").reset_index(drop=True)


def get_pareto_analysis(profiles: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    """Return exact cumulative customer/revenue shares and concentration metrics."""
    if profiles.empty:
        return pd.DataFrame(columns=["customer_share", "revenue_share"]), {}
    ranked = profiles.sort_values(["monetary", "customer_unique_id"], ascending=[False, True]).copy()
    revenue = ranked["monetary"].clip(lower=0)
    total = float(revenue.sum())
    ranked["customer_share"] = 100 * np.arange(1, len(ranked) + 1) / len(ranked)
    ranked["revenue_share"] = 100 * revenue.cumsum() / total if total > 0 else 0.0
    at_80 = ranked.loc[ranked["revenue_share"] >= 80, "customer_share"]
    top_ten_count = max(1, int(np.ceil(len(ranked) * .10)))
    top_ten = ranked.iloc[:top_ten_count]["monetary"].sum()
    metrics = {
        "customers_for_80pct_revenue": float(at_80.iloc[0]) if not at_80.empty else 100.0,
        "top_10pct_revenue_share": float(100 * top_ten / total) if total > 0 else 0.0,
    }
    points = ranked.iloc[np.unique(np.linspace(0, len(ranked) - 1, min(1000, len(ranked))).astype(int))]
    return points[["customer_share", "revenue_share"]].reset_index(drop=True), metrics


def get_segment_geography(profiles: pd.DataFrame, min_customers: int = 25) -> pd.DataFrame:
    """Return state/segment counts with a conservative state sample guardrail."""
    if profiles.empty:
        return pd.DataFrame(columns=["state", "segment", "customers", "revenue"])
    result = profiles.groupby(["state", "segment"], observed=True, as_index=False).agg(
        customers=("customer_unique_id", "nunique"), revenue=("monetary", "sum"))
    return result.loc[result["customers"] >= min_customers].sort_values("customers", ascending=False)


def get_value_matrix_sample(profiles: pd.DataFrame, per_segment: int = 350) -> pd.DataFrame:
    """Deterministically thin dense customer points for browser-safe visualization."""
    samples = []
    for _, group in profiles.sort_values("customer_unique_id").groupby("segment", observed=True):
        if len(group) <= per_segment:
            samples.append(group)
        else:
            indices = np.linspace(0, len(group) - 1, per_segment).astype(int)
            samples.append(group.iloc[indices])
    return pd.concat(samples, ignore_index=True) if samples else profiles.head(0)


def get_customer_rfm_profile(profiles: pd.DataFrame, customer_unique_id: str) -> pd.DataFrame:
    """Find one RFM profile without issuing another database query."""
    return profiles.loc[profiles["customer_unique_id"].eq(customer_unique_id)].copy()
