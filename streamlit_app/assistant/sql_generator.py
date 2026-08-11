"""Deterministic SQL templates for approved intents."""
from datetime import date

from streamlit_app.assistant.models import GeneratedQuery, IntentPlan, UnsupportedQuestion
from streamlit_app.services.common import filtered_orders_cte, get_filter_options
from streamlit_app.utils.filters import FilterState


def effective_filters(active: FilterState, plan: IntentPlan) -> FilterState:
    start = plan.start_date or active.start_date
    end = plan.end_date or active.end_date
    if start > end:
        raise UnsupportedQuestion("The requested date scope is invalid.")
    _, _, approved_states, approved_categories = get_filter_options()
    if any(state not in approved_states for state in plan.states):
        raise UnsupportedQuestion("The requested destination state is not in the approved dimension values.")
    if any(category not in approved_categories for category in plan.categories):
        raise UnsupportedQuestion("The requested category is not in the approved dimension values.")
    return FilterState(start, end, plan.states or active.states, plan.categories or active.categories)


def generate_query(plan: IntentPlan, active: FilterState) -> tuple[GeneratedQuery, FilterState]:
    filters = effective_filters(active, plan); cte, params = filtered_orders_cte(filters)
    limit = min(max(plan.limit, 1), 25)
    if plan.metadata is None:
        raise UnsupportedQuestion("Validated query metadata is required.")
    metadata = plan.metadata
    direction_sql = "ASC" if metadata.ranking_direction == "ascending" else "DESC"
    monthly_templates = {
        "payment_revenue": "SELECT date_trunc('month',f.order_purchase_timestamp)::date AS month,COALESCE(SUM(v.payment_revenue),0) AS payment_revenue FROM filtered_orders f LEFT JOIN order_revenue v ON v.order_id=f.order_id GROUP BY 1 ORDER BY month LIMIT 100",
        "orders": "SELECT date_trunc('month',f.order_purchase_timestamp)::date AS month,COUNT(DISTINCT f.order_id) AS orders FROM filtered_orders f GROUP BY 1 ORDER BY month LIMIT 100",
        "average_order_value": "SELECT date_trunc('month',f.order_purchase_timestamp)::date AS month,COALESCE(SUM(v.payment_revenue)/NULLIF(COUNT(DISTINCT f.order_id),0),0) AS average_order_value FROM filtered_orders f LEFT JOIN order_revenue v ON v.order_id=f.order_id GROUP BY 1 ORDER BY month LIMIT 100",
        "unique_customers": "SELECT date_trunc('month',f.order_purchase_timestamp)::date AS month,COUNT(DISTINCT f.customer_unique_id) AS unique_customers FROM filtered_orders f GROUP BY 1 ORDER BY month LIMIT 100",
        "delivery_rate": "SELECT date_trunc('month',f.order_purchase_timestamp)::date AS month,100.0*COUNT(*) FILTER(WHERE f.order_status='delivered')/NULLIF(COUNT(*),0) AS delivery_rate FROM filtered_orders f GROUP BY 1 ORDER BY month LIMIT 100",
        "late_delivery_rate": "SELECT date_trunc('month',f.order_purchase_timestamp)::date AS month,100.0*COUNT(*) FILTER(WHERE d.delivery_performance='late')/NULLIF(COUNT(*) FILTER(WHERE d.delivery_performance<>'not_delivered'),0) AS late_delivery_rate FROM filtered_orders f JOIN delivery_metrics d ON d.order_id=f.order_id GROUP BY 1 ORDER BY month LIMIT 100",
        "average_delivery_days": "SELECT date_trunc('month',f.order_purchase_timestamp)::date AS month,AVG(d.actual_delivery_days) AS average_delivery_days FROM filtered_orders f JOIN delivery_metrics d ON d.order_id=f.order_id GROUP BY 1 ORDER BY month LIMIT 100",
        "average_review_score": "SELECT date_trunc('month',r.review_creation_date)::date AS month,AVG(r.review_score) AS average_review_score FROM filtered_orders f JOIN olist_analytics.order_reviews r ON r.order_id=f.order_id GROUP BY 1 ORDER BY month LIMIT 100",
        "negative_review_rate": "SELECT date_trunc('month',r.review_creation_date)::date AS month,100.0*COUNT(*) FILTER(WHERE r.review_score<=2)/NULLIF(COUNT(*),0) AS negative_review_rate FROM filtered_orders f JOIN olist_analytics.order_reviews r ON r.order_id=f.order_id GROUP BY 1 ORDER BY month LIMIT 100",
    }
    templates = {
        "total_revenue": ("SELECT COALESCE(SUM(v.payment_revenue),0) AS total_revenue FROM filtered_orders f LEFT JOIN order_revenue v ON v.order_id=f.order_id", "total_revenue", "kpi"),
        "total_orders": ("SELECT COUNT(DISTINCT f.order_id) AS total_orders FROM filtered_orders f", "total_orders", "kpi"),
        "unique_customers": ("SELECT COUNT(DISTINCT f.customer_unique_id) AS unique_customers FROM filtered_orders f", "unique_customers", "kpi"),
        "aov": ("SELECT COALESCE(SUM(v.payment_revenue)/NULLIF(COUNT(DISTINCT f.order_id),0),0) AS average_order_value FROM filtered_orders f LEFT JOIN order_revenue v ON v.order_id=f.order_id", "aov", "kpi"),
        "delivery_rate": ("SELECT 100.0*COUNT(*) FILTER(WHERE f.order_status='delivered')/NULLIF(COUNT(*),0) AS delivery_rate FROM filtered_orders f", "delivery_rate", "kpi"),
        "late_delivery_rate": ("SELECT 100.0*COUNT(*) FILTER(WHERE d.delivery_performance='late')/NULLIF(COUNT(*) FILTER(WHERE d.delivery_performance<>'not_delivered'),0) AS late_delivery_rate FROM filtered_orders f JOIN delivery_metrics d ON d.order_id=f.order_id", "late_delivery_rate", "kpi"),
        "average_review_score": ("SELECT AVG(r.review_score) AS average_review_score FROM filtered_orders f JOIN olist_analytics.order_reviews r ON r.order_id=f.order_id", "average_review_score", "kpi"),
        "negative_review_rate": ("SELECT 100.0*COUNT(*) FILTER(WHERE r.review_score<=2)/NULLIF(COUNT(*),0) AS negative_review_rate FROM filtered_orders f JOIN olist_analytics.order_reviews r ON r.order_id=f.order_id", "negative_review_rate", "kpi"),
        "top_states": (f"SELECT f.customer_state AS state,SUM(v.payment_revenue) AS payment_revenue,COUNT(DISTINCT f.order_id) AS orders FROM filtered_orders f LEFT JOIN order_revenue v ON v.order_id=f.order_id GROUP BY f.customer_state ORDER BY {metadata.metric} {direction_sql} LIMIT %s", metadata.metric, "bar"),
        "monthly_revenue": ("SELECT date_trunc('month',f.order_purchase_timestamp)::date AS month,SUM(v.payment_revenue) AS payment_revenue,COUNT(DISTINCT f.order_id) AS orders FROM filtered_orders f LEFT JOIN order_revenue v ON v.order_id=f.order_id GROUP BY 1 ORDER BY month LIMIT 100", "total_revenue", "line"),
        "payment_distribution": ("SELECT p.payment_type,COUNT(DISTINCT p.order_id) AS orders,SUM(p.payment_value) AS payment_value FROM filtered_orders f JOIN olist_analytics.order_payments p ON p.order_id=f.order_id GROUP BY p.payment_type ORDER BY orders DESC LIMIT 25", "payment_usage", "donut"),
        "top_categories": (f"SELECT COALESCE(t.product_category_name_english,p.product_category_name) AS category,SUM(i.price) AS merchandise_revenue,COUNT(DISTINCT i.order_id) AS orders FROM filtered_orders f JOIN olist_analytics.order_items i ON i.order_id=f.order_id JOIN olist_analytics.products p ON p.product_id=i.product_id LEFT JOIN olist_analytics.product_category_translation t ON t.product_category_name=p.product_category_name GROUP BY 1 ORDER BY {metadata.metric} {direction_sql} LIMIT %s", metadata.metric, "bar"),
        "top_sellers": (f"SELECT i.seller_id,s.seller_state,SUM(i.price) AS merchandise_revenue,COUNT(DISTINCT i.order_id) AS orders FROM filtered_orders f JOIN olist_analytics.order_items i ON i.order_id=f.order_id JOIN olist_analytics.sellers s ON s.seller_id=i.seller_id GROUP BY i.seller_id,s.seller_state ORDER BY {metadata.metric} {direction_sql} LIMIT %s", metadata.metric, "bar"),
        "peak_orders_month": (f"SELECT date_trunc('month',f.order_purchase_timestamp)::date AS month,COUNT(DISTINCT f.order_id) AS orders FROM filtered_orders f GROUP BY 1 ORDER BY orders {direction_sql} LIMIT 1", "total_orders", "table"),
        "late_states": (f"SELECT f.customer_state AS state,100.0*COUNT(*) FILTER(WHERE d.delivery_performance='late')/NULLIF(COUNT(*) FILTER(WHERE d.delivery_performance<>'not_delivered'),0) AS late_delivery_rate,COUNT(*) FILTER(WHERE d.delivery_performance<>'not_delivered') AS eligible_orders FROM filtered_orders f JOIN delivery_metrics d ON d.order_id=f.order_id GROUP BY f.customer_state HAVING COUNT(*) FILTER(WHERE d.delivery_performance<>'not_delivered')>=100 ORDER BY late_delivery_rate {direction_sql} LIMIT %s", "late_delivery_rate", "bar"),
        "compare_states": ("SELECT f.customer_state AS state,SUM(v.payment_revenue) AS payment_revenue,COUNT(DISTINCT f.order_id) AS orders,COUNT(DISTINCT f.customer_unique_id) AS unique_customers,SUM(v.payment_revenue)/NULLIF(COUNT(DISTINCT f.order_id),0) AS average_order_value FROM filtered_orders f LEFT JOIN order_revenue v ON v.order_id=f.order_id GROUP BY f.customer_state ORDER BY payment_revenue DESC LIMIT 2", "total_revenue", "bar"),
        "category_reviews": (f", review_category AS (SELECT DISTINCT r.review_id,COALESCE(t.product_category_name_english,p.product_category_name) AS category,r.review_score FROM filtered_orders f JOIN olist_analytics.order_reviews r ON r.order_id=f.order_id JOIN olist_analytics.order_items i ON i.order_id=f.order_id JOIN olist_analytics.products p ON p.product_id=i.product_id LEFT JOIN olist_analytics.product_category_translation t ON t.product_category_name=p.product_category_name) SELECT category,AVG(review_score) AS average_review_score,COUNT(*) AS reviews FROM review_category GROUP BY category HAVING COUNT(*)>=30 ORDER BY average_review_score {direction_sql} LIMIT %s", "average_review_score", "bar"),
    }
    if plan.intent not in templates:
        if plan.intent == "monthly_trend" and metadata.metric in monthly_templates:
            return GeneratedQuery(cte + monthly_templates[metadata.metric], params, metadata.metric, metadata), filters
        raise UnsupportedQuestion("The approved semantic layer does not contain that query intent.")
    body, metric, chart = templates[plan.intent]
    limit_param_intents = {"top_states", "top_categories", "top_sellers", "late_states", "category_reviews"}
    query_params = (*params, limit) if plan.intent in limit_param_intents else params
    return GeneratedQuery(cte + body, query_params, metric, metadata), filters
