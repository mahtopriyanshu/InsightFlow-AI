"""Domain rules that convert verified metrics into structured insights."""
from typing import Callable

import pandas as pd

from streamlit_app.insights.comparisons import (
    absolute_change, percentage_change, percentage_point_change,
    period_label, previous_comparable_period, safe_float, scope_label,
)
from streamlit_app.insights.config import (
    CRITICAL_RATE_POINT_CHANGE, EXECUTIVE_LIMIT, MEANINGFUL_DAY_CHANGE,
    MEANINGFUL_PERCENT_CHANGE, MEANINGFUL_SCORE_CHANGE,
    MIN_CATEGORY_REVIEWS, MIN_RELATIONSHIP_REVIEWS, MIN_SELLER_ORDERS,
    MIN_STATE_ORDERS, PAGE_LIMIT, WARNING_RATE_POINT_CHANGE,
)
from streamlit_app.insights.models import Evidence, Insight
from streamlit_app.services.common import get_filter_options
from streamlit_app.services.customers import get_customer_metrics
from streamlit_app.services.operations import get_delivery_metrics, get_review_metrics
from streamlit_app.services.overview import get_kpis, get_sales_summary
from streamlit_app.utils.filters import FilterState
from streamlit_app.utils.formatting import currency, number, percentage


def _comparison_filters(filters: FilterState):
    available_start, _, _, _ = get_filter_options()
    return previous_comparable_period(filters, available_start)


def _finalize(insights: list[Insight], limit: int) -> list[Insight]:
    return sorted(insights, key=lambda item: item.priority, reverse=True)[:limit]


def _movement(
    *, title: str, metric: str, current, previous, formatter: Callable,
    filters: FilterState, previous_filters: FilterState, higher_is_better: bool,
    icon: str, priority: float = 70,
) -> Insight | None:
    delta = percentage_change(current, previous)
    if delta is None:
        return None
    direction = "increased" if delta > 0 else "declined" if delta < 0 else "was unchanged"
    favorable = delta > 0 if higher_is_better else delta < 0
    severity = "neutral"
    if abs(delta) >= MEANINGFUL_PERCENT_CHANGE:
        severity = "positive" if favorable else "warning"
    message = (
        f"{title} {direction} {abs(delta):.1f}% versus the previous comparable period."
        if delta else f"{title} was unchanged versus the previous comparable period."
    )
    return Insight(
        title=title, message=message, kind="trend", severity=severity,
        metric=metric, current_value=safe_float(current),
        comparison_value=safe_float(previous), delta=delta,
        evidence=Evidence(
            current_value=formatter(current), previous_value=formatter(previous),
            difference=f"{delta:+.1f}%", period=period_label(filters),
            comparison_period=period_label(previous_filters),
        ), scope=scope_label(filters), supporting_label=f"{delta:+.1f}%",
        icon=icon, priority=priority + min(abs(delta), 30),
    )


def _point_movement(
    *, title: str, metric: str, current, previous, filters: FilterState,
    previous_filters: FilterState, adverse_when_positive: bool, unit: str,
    formatter: Callable, icon: str, priority: float = 75,
) -> Insight | None:
    delta = percentage_point_change(current, previous)
    if delta is None:
        return None
    adverse = delta > 0 if adverse_when_positive else delta < 0
    severity = "neutral"
    if adverse and abs(delta) >= CRITICAL_RATE_POINT_CHANGE:
        severity = "critical"
    elif adverse and abs(delta) >= WARNING_RATE_POINT_CHANGE:
        severity = "warning"
    elif not adverse and abs(delta) >= WARNING_RATE_POINT_CHANGE:
        severity = "positive"
    direction = "increased" if delta > 0 else "decreased" if delta < 0 else "was unchanged"
    message = f"{title} {direction} by {abs(delta):.1f} {unit} versus the previous comparable period."
    return Insight(
        title=title, message=message, kind="risk" if adverse else "trend",
        severity=severity, metric=metric, current_value=safe_float(current),
        comparison_value=safe_float(previous), delta=delta,
        evidence=Evidence(
            current_value=formatter(current), previous_value=formatter(previous),
            difference=f"{delta:+.1f} {unit}", period=period_label(filters),
            comparison_period=period_label(previous_filters),
        ), scope=scope_label(filters), supporting_label=f"{delta:+.1f} {unit}",
        icon=icon, priority=priority + min(abs(delta) * 4, 25),
    )


def _leader(title: str, message: str, metric: str, value, filters: FilterState,
            *, formatted: str, sample_size: int | None = None, icon: str = "🏆",
            priority: float = 55) -> Insight:
    return Insight(
        title=title, message=message, kind="leader", severity="informational",
        metric=metric, current_value=value,
        evidence=Evidence(current_value=formatted, period=period_label(filters),
                          sample_size=sample_size),
        scope=scope_label(filters), supporting_label=formatted,
        icon=icon, priority=priority,
    )


def executive_insights(filters: FilterState, kpis: pd.DataFrame,
                       categories: pd.DataFrame, states: pd.DataFrame,
                       payments: pd.DataFrame,
                       customer_mix: pd.DataFrame | None = None) -> list[Insight]:
    row = kpis.iloc[0]
    insights: list[Insight] = []
    comparison = _comparison_filters(filters)
    if comparison.available:
        previous = get_kpis(comparison.previous).iloc[0]
        for args in (
            ("Revenue", "revenue", row["total_revenue"], previous["total_revenue"], currency, True, "↗", 90),
            ("Order volume", "orders", row["total_orders"], previous["total_orders"], number, True, "▥", 82),
            ("Average order value", "aov", row["average_order_value"], previous["average_order_value"], currency, True, "◫", 72),
            ("Unique customers", "customers", row["unique_customers"], previous["unique_customers"], number, True, "♙", 78),
        ):
            item = _movement(title=args[0], metric=args[1], current=args[2], previous=args[3], formatter=args[4], filters=filters, previous_filters=comparison.previous, higher_is_better=args[5], icon=args[6], priority=args[7])
            if item: insights.append(item)
        delivery = _point_movement(title="Delivery rate", metric="delivery_rate", current=row["delivery_rate"], previous=previous["delivery_rate"], filters=filters, previous_filters=comparison.previous, adverse_when_positive=False, unit="pp", formatter=percentage, icon="✓", priority=80)
        review_delta = absolute_change(row["average_review_score"], previous["average_review_score"])
        if review_delta is not None and abs(review_delta) >= MEANINGFUL_SCORE_CHANGE:
            insights.append(Insight("Review score movement", f"Average review score {'increased' if review_delta > 0 else 'decreased'} by {abs(review_delta):.2f} points versus the previous comparable period.", "trend", "positive" if review_delta > 0 else "warning", "average_review_score", safe_float(row["average_review_score"]), safe_float(previous["average_review_score"]), review_delta, Evidence(number(row["average_review_score"], 2), number(previous["average_review_score"], 2), f"{review_delta:+.2f} points", period_label(filters), period_label(comparison.previous)), scope_label(filters), f"{review_delta:+.2f}", "★", 76 + abs(review_delta) * 10))
        if delivery: insights.append(delivery)
    if not categories.empty:
        top = categories.iloc[0]
        insights.append(_leader("Category leader", f"{top['category']} generated the highest merchandise revenue in the selected data.", "category_revenue", str(top["category"]), filters, formatted=currency(top["revenue"]), sample_size=int(top["orders"]), icon="🏆", priority=65))
    if not states.empty:
        top = states.iloc[0]
        share = 100 * float(top["revenue"]) / max(float(row["total_revenue"]), 1)
        insights.append(_leader("Leading revenue state", f"{top['state']} contributed {share:.1f}% of payment revenue in the selected data.", "state_revenue_share", str(top["state"]), filters, formatted=percentage(share), sample_size=int(top["orders"]), icon="⌖", priority=68))
    if not payments.empty:
        top = payments.iloc[0]
        share = 100 * float(top["payment_value"]) / max(float(payments["payment_value"].astype(float).sum()), 1)
        insights.append(_leader("Payment-method leader", f"{top['payment_type']} represented {share:.1f}% of recorded payment value.", "payment_share", str(top["payment_type"]), filters, formatted=percentage(share), sample_size=int(top["orders"]), icon="◫", priority=58))
    if customer_mix is not None and not customer_mix.empty:
        repeat = customer_mix.loc[customer_mix["customer_type"].eq("Repeat customers")]
        total = float(customer_mix["customers"].astype(float).sum())
        if not repeat.empty and total:
            share = 100 * float(repeat.iloc[0]["customers"]) / total
            insights.append(_leader("Customer mix", f"Repeat customers represent {share:.1f}% of customers in the selected data.", "repeat_customer_share", share, filters, formatted=percentage(share), sample_size=int(total), icon="↻", priority=60))
    return _finalize(insights, EXECUTIVE_LIMIT)


def sales_insights(filters: FilterState, summary: pd.DataFrame,
                   monthly: pd.DataFrame, categories: pd.DataFrame,
                   states: pd.DataFrame, payments: pd.DataFrame) -> list[Insight]:
    row = summary.iloc[0]
    insights: list[Insight] = []
    comparison = _comparison_filters(filters)
    if comparison.available:
        previous = get_sales_summary(comparison.previous).iloc[0]
        for title, metric, current, old, fmt, priority in (
            ("Revenue", "revenue", row["total_revenue"], previous["total_revenue"], currency, 95),
            ("Order volume", "orders", row["total_orders"], previous["total_orders"], number, 85),
            ("Average order value", "aov", row["average_order_value"], previous["average_order_value"], currency, 78),
        ):
            item = _movement(title=title, metric=metric, current=current, previous=old, formatter=fmt, filters=filters, previous_filters=comparison.previous, higher_is_better=True, icon="↗", priority=priority)
            if item: insights.append(item)
    if not monthly.empty:
        peak = monthly.loc[monthly["revenue"].astype(float).idxmax()]
        insights.append(_leader("Peak sales period", f"{pd.to_datetime(peak['month']):%B %Y} recorded the highest monthly revenue.", "peak_month", str(peak["month"]), filters, formatted=currency(peak["revenue"]), sample_size=int(peak["orders"]), icon="▥", priority=72))
    if not categories.empty:
        top = categories.iloc[0]
        insights.append(_leader("Top revenue category", f"{top['category']} leads category merchandise revenue.", "category_revenue", str(top["category"]), filters, formatted=currency(top["revenue"]), sample_size=int(top["orders"]), priority=68))
    if not states.empty:
        top = states.iloc[0]
        insights.append(_leader("Strongest revenue market", f"{top['state']} is the largest payment-revenue state in the selected data.", "state_revenue", str(top["state"]), filters, formatted=currency(top["revenue"]), sample_size=int(top["orders"]), icon="⌖", priority=66))
    if not payments.empty:
        top = payments.iloc[0]
        total = float(payments["payment_value"].astype(float).sum())
        share = 100 * float(top["payment_value"]) / max(total, 1)
        insights.append(_leader("Payment concentration", f"{top['payment_type']} accounts for {share:.1f}% of recorded payment value.", "payment_share", str(top["payment_type"]), filters, formatted=percentage(share), sample_size=int(top["orders"]), icon="◫", priority=62))
    return _finalize(insights, PAGE_LIMIT)


def customer_insights(filters: FilterState, metrics: pd.DataFrame,
                      locations: pd.DataFrame, top_customers: pd.DataFrame,
                      rfm_summary: pd.DataFrame | None = None,
                      pareto_metrics: dict[str, float] | None = None,
                      rfm_geography: pd.DataFrame | None = None) -> list[Insight]:
    row = metrics.iloc[0]
    insights: list[Insight] = []
    comparison = _comparison_filters(filters)
    if comparison.available:
        previous = get_customer_metrics(comparison.previous).iloc[0]
        for title, metric, current, old, fmt, priority in (
            ("Unique customers", "unique_customers", row["unique_customers"], previous["unique_customers"], number, 86),
            ("Revenue per customer", "revenue_per_customer", row["revenue_per_customer"], previous["revenue_per_customer"], currency, 82),
        ):
            item = _movement(title=title, metric=metric, current=current, previous=old, formatter=fmt, filters=filters, previous_filters=comparison.previous, higher_is_better=True, icon="♙", priority=priority)
            if item: insights.append(item)
        repeat = _point_movement(title="Repeat-customer rate", metric="repeat_rate", current=row["repeat_rate"], previous=previous["repeat_rate"], filters=filters, previous_filters=comparison.previous, adverse_when_positive=False, unit="pp", formatter=percentage, icon="↻", priority=78)
        if repeat: insights.append(repeat)
    insights.append(_leader("Repeat-customer mix", f"Repeat customers represent {percentage(row['repeat_rate'])} of customers in the selected data.", "repeat_rate", safe_float(row["repeat_rate"]), filters, formatted=percentage(row["repeat_rate"]), sample_size=int(row["unique_customers"]), icon="↻", priority=58))
    if not locations.empty:
        by_state = locations.groupby("state", as_index=False).agg(customers=("customers", "sum"), orders=("orders", "sum")).sort_values("customers", ascending=False)
        top = by_state.iloc[0]
        share = 100 * float(top["customers"]) / max(float(by_state["customers"].sum()), 1)
        insights.append(_leader("Largest customer state", f"{top['state']} contains {share:.1f}% of customers represented in the selected geography.", "customer_state_share", str(top["state"]), filters, formatted=percentage(share), sample_size=int(top["customers"]), icon="⌖", priority=64))
    if not top_customers.empty:
        top = top_customers.iloc[0]
        short_id = f"{str(top['customer_unique_id'])[:8]}…"
        insights.append(_leader("Highest-value customer", f"Customer {short_id} has the highest revenue in the selected customer ranking.", "customer_revenue", str(top["customer_unique_id"]), filters, formatted=currency(top["revenue"]), sample_size=int(top["orders"]), icon="♙", priority=52))
    if rfm_summary is not None and not rfm_summary.empty:
        champions = rfm_summary.loc[rfm_summary["segment"].astype(str).eq("Champions")]
        if not champions.empty:
            champion = champions.iloc[0]
            insights.append(Insight(
                "Champion contribution",
                f"Champions represent {float(champion['customer_share']):.1f}% of customers and contribute {float(champion['revenue_share']):.1f}% of selected revenue.",
                "mix", "positive", "champion_revenue_share", float(champion["revenue_share"]),
                float(champion["customer_share"]), evidence=Evidence(
                    f"Revenue share: {percentage(champion['revenue_share'])}; customer share: {percentage(champion['customer_share'])}",
                    period=period_label(filters), sample_size=int(champion["customers"])),
                scope=scope_label(filters), supporting_label=percentage(champion["revenue_share"]),
                icon="◆", priority=94))
        at_risk = rfm_summary.loc[rfm_summary["segment"].astype(str).eq("At Risk")]
        if not at_risk.empty:
            risk = at_risk.iloc[0]
            insights.append(Insight(
                "Historical RFM watch",
                f"Customers classified as At Risk by historical RFM behavior represent {float(risk['customer_share']):.1f}% of the selected customer base.",
                "risk", "warning", "at_risk_customer_share", float(risk["customer_share"]),
                evidence=Evidence(percentage(risk["customer_share"]), period=period_label(filters),
                                  sample_size=int(risk["customers"])),
                scope=scope_label(filters), supporting_label=percentage(risk["customer_share"]),
                icon="!", priority=91))
    if pareto_metrics and pareto_metrics.get("customers_for_80pct_revenue") is not None:
        share = float(pareto_metrics["customers_for_80pct_revenue"])
        insights.append(Insight(
            "Customer revenue concentration",
            f"{share:.1f}% of customers account for 80% of selected customer revenue.",
            "mix", "informational", "customers_for_80pct_revenue", share,
            evidence=Evidence(f"Customer share at 80% revenue: {percentage(share)}", period=period_label(filters),
                              sample_size=int(row["unique_customers"])),
            scope=scope_label(filters), supporting_label=percentage(share), icon="◒", priority=88))
    if rfm_geography is not None and not rfm_geography.empty:
        champion_states = rfm_geography.loc[rfm_geography["segment"].astype(str).eq("Champions")]
        if not champion_states.empty:
            state = champion_states.sort_values("customers", ascending=False).iloc[0]
            insights.append(_leader(
                "Champion geography",
                f"{state['state']} contains the largest qualifying group of Champion customers.",
                "champion_state", str(state["state"]), filters, formatted=number(state["customers"]),
                sample_size=int(state["customers"]), icon="⌖", priority=73))
    return _finalize(insights, PAGE_LIMIT)


def product_insights(filters: FilterState, performance: pd.DataFrame,
                     review_categories: pd.DataFrame) -> list[Insight]:
    insights: list[Insight] = []
    if performance.empty:
        return insights
    top_revenue = performance.loc[performance["revenue"].astype(float).idxmax()]
    top_orders = performance.loc[performance["orders"].astype(float).idxmax()]
    total_revenue = float(performance["revenue"].astype(float).sum())
    share = 100 * float(top_revenue["revenue"]) / max(total_revenue, 1)
    insights.append(_leader("Top revenue category", f"{top_revenue['category']} contributes {share:.1f}% of category merchandise revenue.", "category_revenue_share", str(top_revenue["category"]), filters, formatted=percentage(share), sample_size=int(top_revenue["orders"]), priority=85))
    insights.append(_leader("Top order category", f"{top_orders['category']} appears in the most orders in the selected data.", "category_orders", str(top_orders["category"]), filters, formatted=number(top_orders["orders"]), sample_size=int(top_orders["orders"]), icon="▥", priority=72))
    qualifying = review_categories.loc[review_categories["reviews"].astype(float) >= MIN_CATEGORY_REVIEWS]
    if not qualifying.empty:
        best = qualifying.loc[qualifying["average_review_score"].astype(float).idxmax()]
        lowest = qualifying.loc[qualifying["average_review_score"].astype(float).idxmin()]
        insights.append(_leader("Best-reviewed qualifying category", f"{best['category']} has the highest average score among categories with at least {MIN_CATEGORY_REVIEWS} reviews.", "category_review", str(best["category"]), filters, formatted=f"{number(best['average_review_score'], 2)} ★", sample_size=int(best["reviews"]), icon="★", priority=65))
        insights.append(Insight("Category review watch", f"{lowest['category']} has the lowest average score among qualifying categories; this is a ranking, not a causal diagnosis.", "risk", "warning", "category_review", str(lowest["category"]), evidence=Evidence(f"{number(lowest['average_review_score'], 2)} ★", period=period_label(filters), sample_size=int(lowest["reviews"])), scope=scope_label(filters), supporting_label=f"{number(lowest['average_review_score'], 2)} ★", icon="!", priority=68))
    freight_pool = performance.loc[performance["items_sold"].astype(float) >= MIN_CATEGORY_REVIEWS]
    if not freight_pool.empty:
        freight = freight_pool.loc[freight_pool["average_freight"].astype(float).idxmax()]
        insights.append(_leader("Freight burden", f"{freight['category']} has the highest average freight among categories with at least {MIN_CATEGORY_REVIEWS} sold items.", "average_freight", str(freight["category"]), filters, formatted=currency(freight["average_freight"]), sample_size=int(freight["items_sold"]), icon="▤", priority=54))
    return _finalize(insights, PAGE_LIMIT)


def seller_insights(filters: FilterState, sellers: pd.DataFrame) -> list[Insight]:
    if sellers.empty:
        return []
    insights: list[Insight] = []
    revenue_leader = sellers.loc[sellers["revenue"].astype(float).idxmax()]
    order_leader = sellers.loc[sellers["orders"].astype(float).idxmax()]
    total = float(sellers["revenue"].astype(float).sum())
    share = 100 * float(revenue_leader["revenue"]) / max(total, 1)
    short_revenue = f"{str(revenue_leader['seller_id'])[:8]}…"
    short_orders = f"{str(order_leader['seller_id'])[:8]}…"
    insights.append(_leader("Top revenue seller", f"Seller {short_revenue} leads the displayed seller set with {share:.1f}% of its revenue.", "seller_revenue", str(revenue_leader["seller_id"]), filters, formatted=currency(revenue_leader["revenue"]), sample_size=int(revenue_leader["orders"]), icon="♧", priority=85))
    insights.append(_leader("Top order seller", f"Seller {short_orders} fulfilled the most orders in the displayed seller set.", "seller_orders", str(order_leader["seller_id"]), filters, formatted=number(order_leader["orders"]), sample_size=int(order_leader["orders"]), icon="▥", priority=72))
    qualifying = sellers.loc[sellers["orders"].astype(float) >= MIN_SELLER_ORDERS]
    if not qualifying.empty:
        weakest = qualifying.loc[qualifying["delivery_rate"].astype(float).idxmin()]
        strongest = qualifying.loc[qualifying["delivery_rate"].astype(float).idxmax()]
        insights.append(Insight("Fulfillment watch", f"Seller {str(weakest['seller_id'])[:8]}… has the lowest delivery rate among sellers with at least {MIN_SELLER_ORDERS} orders.", "risk", "warning" if float(weakest["delivery_rate"]) < 90 else "neutral", "seller_delivery_rate", str(weakest["seller_id"]), evidence=Evidence(percentage(weakest["delivery_rate"]), period=period_label(filters), sample_size=int(weakest["orders"])), scope=scope_label(filters), supporting_label=percentage(weakest["delivery_rate"]), icon="!", priority=76))
        insights.append(_leader("Fulfillment leader", f"Seller {str(strongest['seller_id'])[:8]}… has the highest delivery rate among qualifying sellers.", "seller_delivery_rate", str(strongest["seller_id"]), filters, formatted=percentage(strongest["delivery_rate"]), sample_size=int(strongest["orders"]), icon="✓", priority=55))
    state = sellers.groupby("state", as_index=False).agg(revenue=("revenue", "sum"), sellers=("seller_id", "count")).sort_values("revenue", ascending=False).iloc[0]
    insights.append(_leader("Seller revenue geography", f"{state['state']} contributes the most revenue within the displayed seller set.", "seller_state", str(state["state"]), filters, formatted=currency(state["revenue"]), sample_size=int(state["sellers"]), icon="⌖", priority=58))
    return _finalize(insights, PAGE_LIMIT)


def delivery_insights(filters: FilterState, metrics: pd.DataFrame,
                      by_state: pd.DataFrame) -> list[Insight]:
    row = metrics.iloc[0]
    insights: list[Insight] = []
    comparison = _comparison_filters(filters)
    if comparison.available:
        previous = get_delivery_metrics(comparison.previous).iloc[0]
        for title, metric, current, old, adverse, priority in (
            ("Delivery rate", "delivery_rate", row["delivery_rate"], previous["delivery_rate"], False, 82),
            ("Late-delivery rate", "late_rate", row["late_rate"], previous["late_rate"], True, 96),
        ):
            item = _point_movement(title=title, metric=metric, current=current, previous=old, filters=filters, previous_filters=comparison.previous, adverse_when_positive=adverse, unit="pp", formatter=percentage, icon="!" if adverse else "✓", priority=priority)
            if item: insights.append(item)
        day_delta = absolute_change(row["average_delivery_days"], previous["average_delivery_days"])
        if day_delta is not None and abs(day_delta) >= MEANINGFUL_DAY_CHANGE:
            improved = day_delta < 0
            insights.append(Insight("Average delivery time", f"Average delivery time {'improved' if improved else 'increased'} by {abs(day_delta):.1f} days versus the previous comparable period.", "trend", "positive" if improved else "warning", "average_delivery_days", safe_float(row["average_delivery_days"]), safe_float(previous["average_delivery_days"]), day_delta, Evidence(f"{number(row['average_delivery_days'], 1)} days", f"{number(previous['average_delivery_days'], 1)} days", f"{day_delta:+.1f} days", period_label(filters), period_label(comparison.previous)), scope_label(filters), f"{day_delta:+.1f} days", "🚚", 86 + abs(day_delta) * 3))
    qualifying = by_state.loc[by_state["delivered_orders"].astype(float) >= MIN_STATE_ORDERS].dropna(subset=["late_rate"])
    on_time_rate = 100 - float(row["late_rate"] or 0)
    insights.append(_leader("On-time delivery mix", f"{on_time_rate:.1f}% of eligible delivered orders arrived on time or early.", "on_time_rate", on_time_rate, filters, formatted=percentage(on_time_rate), sample_size=int(row["delivered_orders"]), icon="✓", priority=62))
    if not qualifying.empty:
        worst = qualifying.loc[qualifying["late_rate"].astype(float).idxmax()]
        best = qualifying.loc[qualifying["late_rate"].astype(float).idxmin()]
        insights.append(Insight("Highest late-delivery rate", f"{worst['state']} has the highest late-delivery rate among states with at least {MIN_STATE_ORDERS} eligible deliveries.", "risk", "warning", "state_late_rate", str(worst["state"]), evidence=Evidence(percentage(worst["late_rate"]), period=period_label(filters), sample_size=int(worst["delivered_orders"])), scope=scope_label(filters), supporting_label=percentage(worst["late_rate"]), icon="!", priority=88))
        insights.append(_leader("Lowest late-delivery rate", f"{best['state']} has the lowest late-delivery rate among qualifying states.", "state_late_rate", str(best["state"]), filters, formatted=percentage(best["late_rate"]), sample_size=int(best["delivered_orders"]), icon="✓", priority=58))
    return _finalize(insights, PAGE_LIMIT)


def review_insights(filters: FilterState, metrics: pd.DataFrame,
                    distribution: pd.DataFrame, categories: pd.DataFrame,
                    relationship: pd.DataFrame) -> list[Insight]:
    row = metrics.iloc[0]
    insights: list[Insight] = []
    comparison = _comparison_filters(filters)
    if comparison.available:
        previous = get_review_metrics(comparison.previous).iloc[0]
        score_delta = absolute_change(row["average_review_score"], previous["average_review_score"])
        if score_delta is not None and abs(score_delta) >= MEANINGFUL_SCORE_CHANGE:
            insights.append(Insight("Average review score", f"Average review score {'increased' if score_delta > 0 else 'decreased'} by {abs(score_delta):.2f} points versus the previous comparable period.", "trend", "positive" if score_delta > 0 else "warning", "average_review_score", safe_float(row["average_review_score"]), safe_float(previous["average_review_score"]), score_delta, Evidence(number(row["average_review_score"], 2), number(previous["average_review_score"], 2), f"{score_delta:+.2f} points", period_label(filters), period_label(comparison.previous)), scope_label(filters), f"{score_delta:+.2f}", "★", 86))
        negative = _point_movement(title="Negative-review rate", metric="negative_review_rate", current=row["negative_review_rate"], previous=previous["negative_review_rate"], filters=filters, previous_filters=comparison.previous, adverse_when_positive=True, unit="pp", formatter=percentage, icon="!", priority=92)
        if negative: insights.append(negative)
    total = max(float(row["total_reviews"]), 1)
    five = distribution.loc[distribution["review_score"].eq(5), "reviews"].sum()
    five_rate = 100 * float(five) / total
    insights.append(_leader("Five-star share", f"Five-star reviews represent {five_rate:.1f}% of reviews in the selected data.", "five_star_rate", five_rate, filters, formatted=percentage(five_rate), sample_size=int(total), icon="★", priority=60))
    qualifying = categories.loc[categories["reviews"].astype(float) >= MIN_CATEGORY_REVIEWS]
    if not qualifying.empty:
        best = qualifying.loc[qualifying["average_review_score"].astype(float).idxmax()]
        lowest = qualifying.loc[qualifying["average_review_score"].astype(float).idxmin()]
        insights.append(_leader("Best-reviewed category", f"{best['category']} ranks highest among categories with at least {MIN_CATEGORY_REVIEWS} reviews.", "category_review", str(best["category"]), filters, formatted=f"{number(best['average_review_score'], 2)} ★", sample_size=int(best["reviews"]), icon="★", priority=68))
        insights.append(Insight("Lowest-reviewed category", f"{lowest['category']} ranks lowest among qualifying categories; this does not identify a cause.", "risk", "warning", "category_review", str(lowest["category"]), evidence=Evidence(f"{number(lowest['average_review_score'], 2)} ★", period=period_label(filters), sample_size=int(lowest["reviews"])), scope=scope_label(filters), supporting_label=f"{number(lowest['average_review_score'], 2)} ★", icon="!", priority=72))
    rel = relationship.loc[relationship["reviews"].astype(float) >= MIN_RELATIONSHIP_REVIEWS]
    on_time = rel.loc[rel["delivery_performance"].eq("on_time_or_early")]
    late = rel.loc[rel["delivery_performance"].eq("late")]
    if not on_time.empty and not late.empty:
        on_time_score = float(on_time.iloc[0]["average_review_score"])
        late_score = float(late.iloc[0]["average_review_score"])
        difference = late_score - on_time_score
        insights.append(Insight("Delivery and review association", f"Late-delivered orders average {late_score:.2f} stars versus {on_time_score:.2f} for on-time or early orders in the selected data.", "relationship", "warning" if difference < 0 else "informational", "delivery_review_score", late_score, on_time_score, difference, Evidence(f"Late: {late_score:.2f} ★", f"On time: {on_time_score:.2f} ★", f"{difference:+.2f} points", period_label(filters), sample_size=int(late.iloc[0]["reviews"])), scope_label(filters), f"{difference:+.2f} points", "↔", 94 if difference < 0 else 62))
    return _finalize(insights, PAGE_LIMIT)


def product_pro_insights(filters: FilterState, categories: pd.DataFrame,
                         concentration_metrics: dict[str, float],
                         signals: pd.DataFrame) -> list[Insight]:
    """Convert verified portfolio metrics into Product Pro observations."""
    if categories.empty: return []
    result: list[Insight] = []
    total=float(categories["merchandise_revenue"].sum()); top=categories.iloc[0]
    share=100*float(top["merchandise_revenue"])/max(total,1)
    result.append(_leader("Category contribution",f"{top['category']} contributes {share:.1f}% of selected merchandise revenue.","category_revenue_share",str(top["category"]),filters,formatted=percentage(share),sample_size=int(top["orders"]),priority=95))
    pareto=float(concentration_metrics["entities_for_80"])
    result.append(Insight("Category concentration",f"{pareto:.1f}% of represented categories generate 80% of selected merchandise revenue.","mix","informational","categories_for_80",pareto,evidence=Evidence(percentage(pareto),period=period_label(filters),sample_size=len(categories)),scope=scope_label(filters),supporting_label=percentage(pareto),icon="◒",priority=90))
    risks=signals.loc[signals["signal"].eq("Experience Risk")].sort_values("merchandise_revenue",ascending=False)
    if not risks.empty:
        row=risks.iloc[0]; result.append(Insight("Commercial experience watch",f"{row['category']} has meaningful merchandise revenue but a below-benchmark review score in the qualifying set.","risk","warning","category_experience",str(row["category"]),evidence=Evidence(f"{number(row['average_review_score'],2)} stars",period=period_label(filters),sample_size=int(row["reviews"])),scope=scope_label(filters),supporting_label=currency(row["merchandise_revenue"]),icon="!",priority=88))
    if not signals.empty:
        row=signals.sort_values("freight_ratio",ascending=False).iloc[0]; median=float(signals.attrs.get("freight_median",signals.freight_ratio.median()))
        result.append(Insight("Freight burden",f"{row['category']} has a {float(row['freight_ratio']):.1f}% freight-to-merchandise ratio versus a {median:.1f}% qualifying-category median.","risk","warning" if float(row["freight_ratio"])>median*1.5 else "informational","freight_ratio",float(row["freight_ratio"]),median,float(row["freight_ratio"])-median,Evidence(percentage(row["freight_ratio"]),percentage(median),f"{float(row['freight_ratio'])-median:+.1f} pp",period_label(filters),sample_size=int(row["orders"])),scope_label(filters),percentage(row["freight_ratio"]),"▱",82))
    opportunities=signals.loc[signals["signal"].eq("Opportunity Signal")].sort_values("orders",ascending=False)
    if not opportunities.empty:
        row=opportunities.iloc[0];result.append(_leader("Opportunity signal",f"{row['category']} combines above-benchmark reviews with meaningful order volume and below-median category revenue.","category_opportunity",str(row["category"]),filters,formatted=number(row["orders"]),sample_size=int(row["reviews"]),icon="+",priority=75))
    return _finalize(result,PAGE_LIMIT)


def seller_pro_insights(filters: FilterState, sellers: pd.DataFrame,
                        concentration_metrics: dict[str, float],
                        signals: pd.DataFrame) -> list[Insight]:
    """Convert verified seller economics and fulfillment into observations."""
    if sellers.empty:return []
    result:list[Insight]=[];total=float(sellers.merchandise_revenue.sum());top=sellers.iloc[0]
    share=100*float(top.merchandise_revenue)/max(total,1);short=f"{str(top.seller_id)[:8]}…"
    result.append(_leader("Top revenue seller",f"Seller {short} contributes {share:.1f}% of selected merchandise revenue.","seller_revenue_share",str(top.seller_id),filters,formatted=percentage(share),sample_size=int(top.orders),icon="♧",priority=95))
    pareto=float(concentration_metrics["entities_for_80"])
    result.append(Insight("Seller concentration",f"{pareto:.1f}% of active sellers generate 80% of selected seller merchandise revenue.","mix","warning" if pareto<20 else "informational","sellers_for_80",pareto,evidence=Evidence(percentage(pareto),period=period_label(filters),sample_size=len(sellers)),scope=scope_label(filters),supporting_label=percentage(pareto),icon="◒",priority=90))
    risks=signals.loc[signals.signal.eq("Operational Risk Signal")].sort_values("merchandise_revenue",ascending=False)
    if not risks.empty:
        row=risks.iloc[0];result.append(Insight("Operational risk signal",f"Seller {str(row.seller_id)[:8]}… combines upper-quartile revenue exposure with an above-median late-delivery rate.","risk","warning","seller_fulfillment",str(row.seller_id),evidence=Evidence(percentage(row.late_rate),period=period_label(filters),sample_size=int(row.orders)),scope=scope_label(filters),supporting_label=currency(row.merchandise_revenue),icon="!",priority=92))
    state=sellers.groupby("state",as_index=False).agg(revenue=("merchandise_revenue","sum"),sellers=("seller_id","nunique")).sort_values("revenue",ascending=False).iloc[0]
    state_share=100*float(state.revenue)/max(total,1)
    result.append(_leader("Seller geography",f"{state.state} is the largest seller-location market, contributing {state_share:.1f}% of selected seller revenue.","seller_state_share",str(state.state),filters,formatted=percentage(state_share),sample_size=int(state.sellers),icon="⌖",priority=78))
    return _finalize(result,PAGE_LIMIT)
