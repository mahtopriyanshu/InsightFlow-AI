"""Approved business vocabulary and database allowlists."""
from dataclasses import dataclass
import re

from streamlit_app.assistant.models import IntentPlan, QueryMetadata, UnsupportedQuestion


@dataclass(frozen=True)
class MetricDefinition:
    label: str
    definition: str
    revenue_type: str | None = None


METRICS = {
    "total_revenue": MetricDefinition("Payment revenue", "Sum of validated order payment revenue.", "payment"),
    "total_orders": MetricDefinition("Orders", "Count of distinct filtered order_id values."),
    "unique_customers": MetricDefinition("Unique customers", "Count of distinct customer_unique_id values."),
    "aov": MetricDefinition("Average order value", "Payment revenue divided by distinct orders.", "payment"),
    "delivery_rate": MetricDefinition("Delivery rate", "Delivered order count divided by filtered order count."),
    "late_delivery_rate": MetricDefinition("Late-delivery rate", "Late eligible deliveries divided by all eligible deliveries."),
    "average_review_score": MetricDefinition("Average review score", "Mean order review score for filtered orders."),
    "negative_review_rate": MetricDefinition("Negative-review rate", "Share of review rows with review_score at or below 2."),
    "merchandise_revenue": MetricDefinition("Merchandise revenue", "Sum of order_items.price.", "merchandise"),
    "payment_usage": MetricDefinition("Payment-method usage", "Distinct orders and payment value grouped by payment_type."),
    "payment_revenue": MetricDefinition("Payment revenue", "Sum of validated order payment revenue.", "payment"),
    "orders": MetricDefinition("Orders", "Count of distinct filtered order_id values."),
    "average_order_value": MetricDefinition("Average order value", "Monthly payment revenue divided by distinct monthly orders.", "payment"),
    "average_delivery_days": MetricDefinition("Average delivery days", "Mean actual delivery duration for delivered orders with a recorded duration."),
}

DIMENSIONS = ("month", "customer destination state", "product category", "seller", "payment method")

ALLOWED_TABLES = {
    "orders", "customers", "order_items", "products", "product_category_translation",
    "order_payments", "order_reviews", "sellers", "vw_order_revenue",
    "vw_order_delivery_metrics", "mv_order_revenue",
}

ALLOWED_COLUMNS = {
    "order_id", "customer_id", "customer_unique_id", "customer_state", "customer_city",
    "order_status", "order_purchase_timestamp", "order_delivered_customer_date",
    "order_estimated_delivery_date", "payment_revenue", "merchandise_value", "freight_value",
    "total_item_value", "actual_delivery_days", "delivery_delay_days", "delivery_performance",
    "payment_type", "payment_value", "product_id", "seller_id", "price", "review_id",
    "review_score", "review_creation_date", "product_category_name", "product_category_name_english", "seller_state",
    "seller_city", "state", "category", "month", "revenue", "orders", "customers", "value",
    "rate", "average_order_value", "average_review_score", "reviews", "items_sold",
    "total_revenue", "total_orders", "unique_customers", "merchandise_revenue",
    "late_delivery_rate", "eligible_orders",
}

SUPPORTED_INTENTS = {
    "total_revenue", "total_orders", "unique_customers", "aov", "top_categories",
    "top_states", "monthly_revenue", "payment_distribution", "delivery_rate",
    "late_delivery_rate", "average_review_score", "negative_review_rate", "top_sellers",
    "category_reviews", "compare_states", "peak_orders_month", "late_states", "monthly_trend",
}


@dataclass(frozen=True)
class IntentSpec:
    metrics: tuple[str, ...]
    default_metric: str
    dimension: str
    chart_type: str
    directions: tuple[str, ...] = ("none",)
    default_direction: str = "none"
    time_grain: str | None = None


INTENT_SPECS = {
    "total_revenue": IntentSpec(("total_revenue",), "total_revenue", "scalar", "kpi"),
    "total_orders": IntentSpec(("total_orders",), "total_orders", "scalar", "kpi"),
    "unique_customers": IntentSpec(("unique_customers",), "unique_customers", "scalar", "kpi"),
    "aov": IntentSpec(("aov",), "aov", "scalar", "kpi"),
    "delivery_rate": IntentSpec(("delivery_rate",), "delivery_rate", "scalar", "kpi"),
    "late_delivery_rate": IntentSpec(("late_delivery_rate",), "late_delivery_rate", "scalar", "kpi"),
    "average_review_score": IntentSpec(("average_review_score",), "average_review_score", "scalar", "kpi"),
    "negative_review_rate": IntentSpec(("negative_review_rate",), "negative_review_rate", "scalar", "kpi"),
    "top_categories": IntentSpec(("merchandise_revenue", "orders"), "merchandise_revenue", "category", "bar", ("ascending", "descending"), "descending"),
    "top_states": IntentSpec(("payment_revenue", "orders"), "payment_revenue", "state", "bar", ("ascending", "descending"), "descending"),
    "top_sellers": IntentSpec(("merchandise_revenue", "orders"), "merchandise_revenue", "seller_id", "bar", ("ascending", "descending"), "descending"),
    "late_states": IntentSpec(("late_delivery_rate",), "late_delivery_rate", "state", "bar", ("ascending", "descending"), "descending"),
    "category_reviews": IntentSpec(("average_review_score",), "average_review_score", "category", "bar", ("ascending", "descending"), "ascending"),
    "monthly_revenue": IntentSpec(("payment_revenue",), "payment_revenue", "month", "line", time_grain="month"),
    "monthly_trend": IntentSpec(("payment_revenue", "orders", "average_order_value", "unique_customers", "delivery_rate", "late_delivery_rate", "average_delivery_days", "average_review_score", "negative_review_rate"), "orders", "month", "line", time_grain="month"),
    "payment_distribution": IntentSpec(("orders",), "orders", "payment_type", "donut", ("descending",), "descending"),
    "compare_states": IntentSpec(("payment_revenue",), "payment_revenue", "state", "bar", ("descending",), "descending"),
    "peak_orders_month": IntentSpec(("orders",), "orders", "month", "table", ("ascending", "descending"), "descending", "month"),
}


def _explicit_metric(question: str) -> str | None:
    text = question.lower().replace("-", " ")
    if "average order value" in text or re.search(r"\baov\b", text): return "average_order_value"
    if "average delivery" in text and ("day" in text or "duration" in text): return "average_delivery_days"
    if "unique customer" in text: return "unique_customers"
    if "negative review" in text: return "negative_review_rate"
    if "number of orders" in text or re.search(r"\borders\b", text): return "orders"
    if "average review" in text or "review score" in text: return "average_review_score"
    if "late delivery" in text: return "late_delivery_rate"
    if "delivery rate" in text: return "delivery_rate"
    if "merchandise revenue" in text: return "merchandise_revenue"
    if "revenue" in text: return "payment_revenue"
    return None


def _explicit_direction(question: str) -> str | None:
    text = question.lower()
    if any(word in text for word in ("lowest", "least", "bottom")): return "ascending"
    if any(word in text for word in ("highest", "most", "top", "best")): return "descending"
    if "poor review" in text: return "ascending"
    return None


def validate_plan_metadata(plan: IntentPlan, question: str) -> IntentPlan:
    """Canonicalize LLM/local metadata against the approved intent specification."""
    if plan.intent not in INTENT_SPECS:
        raise UnsupportedQuestion("The approved semantic layer does not define that intent metadata.")
    spec = INTENT_SPECS[plan.intent]; supplied = plan.metadata
    lowered = question.lower()
    trend_language = any(term in lowered for term in ("monthly", "month by month", "over time", "trend by month", "monthly trend", "changed over time"))
    if trend_language and "revenue" in lowered and re.search(r"\borders\b", lowered):
        raise UnsupportedQuestion("Multi-metric monthly trends are not yet approved by the governed semantic layer.")
    if trend_language and "categor" in lowered and ("by category" in lowered or "category month" in lowered):
        raise UnsupportedQuestion("Category-by-month analysis is not yet approved by the governed semantic layer.")
    explicit_metric = _explicit_metric(question)
    if explicit_metric == "payment_revenue" and "total_revenue" in spec.metrics: explicit_metric = "total_revenue"
    if explicit_metric == "orders" and "total_orders" in spec.metrics: explicit_metric = "total_orders"
    if explicit_metric == "average_order_value" and "aov" in spec.metrics: explicit_metric = "aov"
    metric = explicit_metric or (supplied.metric if supplied else spec.default_metric)
    direction = _explicit_direction(question) or (supplied.ranking_direction if supplied else spec.default_direction)
    if metric == "payment_revenue" and plan.intent in {"top_categories", "top_sellers"}:
        metric = "merchandise_revenue"
    if metric not in spec.metrics or direction not in spec.directions:
        raise UnsupportedQuestion("The requested metric or ranking direction is not approved for that intent.")
    metadata = QueryMetadata(metric, spec.dimension, spec.chart_type, direction, spec.time_grain)
    return IntentPlan(plan.intent, plan.limit, plan.states, plan.categories, plan.start_date, plan.end_date, plan.interpretation, metadata)


def semantic_prompt() -> str:
    metrics = "\n".join(f"- {key}: {item.definition}" for key, item in METRICS.items())
    combinations = "\n".join(f"- {key}: metrics={list(spec.metrics)}, dimension={spec.dimension}, chart={spec.chart_type}, directions={list(spec.directions)}, time_grain={spec.time_grain or 'none'}" for key,spec in INTENT_SPECS.items())
    return f"""Approved metrics:\n{metrics}\nApproved dimensions: {', '.join(DIMENSIONS)}.\nApproved intent metadata combinations:\n{combinations}\nIf the request is unsupported, return intent=unsupported. Never invent a metric, dimension, chart type, ranking direction, or field."""
