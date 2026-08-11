"""Deterministic explanations sourced only from verified result rows."""
import pandas as pd
from streamlit_app.assistant.models import IntentPlan
from streamlit_app.assistant.presentation import humanize_entity
from streamlit_app.utils.formatting import currency, number, percentage


def format_answer(plan: IntentPlan, data: pd.DataFrame) -> str:
    row = data.iloc[0]; intent = plan.intent; metadata = plan.metadata
    if intent == "total_revenue": return f"Verified payment revenue is **{currency(row.total_revenue)}** in the effective scope."
    if intent == "total_orders": return f"The effective scope contains **{number(row.total_orders)} distinct orders**."
    if intent == "unique_customers": return f"The effective scope contains **{number(row.unique_customers)} unique customers** at customer_unique_id grain."
    if intent == "aov": return f"Verified average order value is **{currency(row.average_order_value)}**."
    if intent == "delivery_rate": return f"The validated delivery rate is **{percentage(row.delivery_rate)}**."
    if intent == "late_delivery_rate": return f"The late-delivery rate among eligible deliveries is **{percentage(row.late_delivery_rate)}**."
    if intent == "average_review_score": return f"Average order review score is **{number(row.average_review_score, 2)} / 5**."
    if intent == "negative_review_rate": return f"Reviews scored 1–2 represent **{percentage(row.negative_review_rate)}** of review rows."
    if intent in {"top_categories", "top_states", "top_sellers", "late_states", "category_reviews"}:
        entity = row.category if metadata.dimension == "category" else row.state if metadata.dimension == "state" else row.seller_id
        if metadata.dimension == "category": entity = humanize_entity(entity)
        direction = "lowest" if metadata.ranking_direction == "ascending" else "highest"
        if metadata.metric == "orders": value, label = f"{number(row.orders)} orders", "order count"
        elif metadata.metric == "merchandise_revenue": value, label = currency(row.merchandise_revenue), "merchandise revenue"
        elif metadata.metric == "payment_revenue": value, label = currency(row.payment_revenue), "payment revenue"
        elif metadata.metric == "late_delivery_rate": value, label = percentage(row.late_delivery_rate), "late-delivery rate"
        else: value, label = f"{number(row.average_review_score,2)} / 5", "average review score"
        guardrail = " among categories meeting the 30-review guardrail" if intent == "category_reviews" else " among the returned results"
        return f"**{entity}** has the {direction} {label}{guardrail} at **{value}**."
    if intent in {"monthly_revenue", "monthly_trend"}:
        metric = metadata.metric; values = data[metric].astype(float); peak = data.loc[values.idxmax()]
        value = peak[metric]
        if metric in {"payment_revenue", "average_order_value"}: formatted = currency(value)
        elif metric in {"delivery_rate", "late_delivery_rate", "negative_review_rate"}: formatted = percentage(value)
        elif metric == "average_delivery_days": formatted = f"{number(value, 1)} days"
        elif metric == "average_review_score": formatted = f"{number(value, 2)} / 5"
        else: formatted = number(value)
        label = metadata.metric.replace("_", " ")
        return f"The complete scoped monthly series contains **{len(data)} periods**. The highest observed {label} was **{formatted}** in **{pd.Timestamp(peak.month):%B %Y}**. Boundary months may represent partial selected periods."
    if intent == "payment_distribution": return f"**{row.payment_type}** appears on the most distinct orders in the verified payment distribution."
    if intent == "compare_states":
        if len(data) < 2: return "Only one requested destination state had verified data in the effective scope."
        return f"**{data.iloc[0].state}** generated {currency(data.iloc[0].payment_revenue)}, compared with **{data.iloc[1].state}** at {currency(data.iloc[1].payment_revenue)}."
    if intent == "peak_orders_month":
        direction = "lowest" if metadata.ranking_direction == "ascending" else "highest"
        return f"**{pd.Timestamp(row.month):%B %Y}** had the {direction} observed order count at **{number(row.orders)} orders**."
    return f"The verified query returned {len(data)} rows."
