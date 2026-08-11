"""Question safety checks and approved-intent planning."""
from datetime import date
import json
import logging
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import quote

from streamlit_app.assistant.config import AISettings
from streamlit_app.assistant.models import AssistantUnavailable, IntentPlan, QueryMetadata, UnsafeQuestion, UnsupportedQuestion
from streamlit_app.assistant.semantic import SUPPORTED_INTENTS, semantic_prompt, validate_plan_metadata

ADVERSARIAL = (
    r"ignore (all |the )?(previous|prior) instructions", r"\bdrop\s+(table|schema|database)\b",
    r"\bdelete\s+from\b", r"\binsert\s+into\b", r"\bupdate\s+\w+\s+set\b",
    r"\bcopy\s+.+\s+to\b", r"\bpg_catalog\b", r"\binformation_schema\b",
    r"environment variables?", r"database credentials?", r"read.*secret",
)
UNSUPPORTED = ("inventory", "viral", "will churn", "caused", "cause this customer", "delivery company", "carrier", "environment variable")
CAUSAL_QUESTION = re.compile(r"\b(why|what caused|cause of|because)\b", re.IGNORECASE)
LOGGER = logging.getLogger(__name__)


def precheck_question(question: str):
    clean = question.strip()
    if not clean:
        raise UnsupportedQuestion("Enter a business analytics question.")
    lowered = clean.lower()
    if any(re.search(pattern, lowered, re.DOTALL) for pattern in ADVERSARIAL):
        raise UnsafeQuestion("This instruction is blocked by the assistant security policy.")
    if any(term in lowered for term in UNSUPPORTED):
        raise UnsupportedQuestion("The approved dataset and semantic layer do not support that analysis.")
    if CAUSAL_QUESTION.search(clean):
        raise UnsupportedQuestion("Causal explanations are not supported by this observational dataset. Ask for a comparison or observed contributors instead.")
    return clean


def _year_scope(text):
    match = re.search(r"\b(20\d{2})\b", text)
    if not match:
        return None, None
    year = int(match.group(1)); return date(year, 1, 1), date(year, 12, 31)


def local_plan(question: str) -> IntentPlan:
    """Deterministic planner used by golden tests, never as a fake LLM response."""
    text = precheck_question(question); lowered = text.lower(); start, end = _year_scope(lowered)
    states = tuple(re.findall(r"\b[A-Z]{2}\b", text))
    limit_match = re.search(r"\b(?:top|bottom)\s+(\d+)\b", lowered) or re.search(r"\b(?:show(?: me)? the|which)\s+(\d+)\b", lowered)
    limit = min(int(limit_match.group(1)), 25) if limit_match else 10
    trend_language = any(term in lowered for term in ("monthly", "month by month", "over time", "trend by month", "monthly trend", "changed over time"))
    highest_or_lowest_month = "month" in lowered and any(term in lowered for term in ("highest", "lowest", "most", "least"))
    if "compare" in lowered and len(states) >= 2: intent = "compare_states"
    elif "late" in lowered and "state" in lowered: intent = "late_states"
    elif highest_or_lowest_month and "orders" in lowered: intent = "peak_orders_month"
    elif "monthly" in lowered and "revenue" in lowered: intent = "monthly_revenue"
    elif trend_language: intent = "monthly_trend"
    elif "payment method" in lowered: intent = "payment_distribution"
    elif "categor" in lowered and ("average review" in lowered or "review score" in lowered or "poor review" in lowered): intent = "category_reviews"
    elif "categor" in lowered and ("revenue" in lowered or "orders" in lowered): intent = "top_categories"
    elif ("top" in lowered or "most" in lowered) and "seller" in lowered: intent = "top_sellers"
    elif "state" in lowered and ("revenue" in lowered or "orders" in lowered): intent = "top_states"
    elif "late delivery rate" in lowered or "late-delivery rate" in lowered: intent = "late_delivery_rate"
    elif "delivery rate" in lowered: intent = "delivery_rate"
    elif "negative review" in lowered or "negative-review" in lowered: intent = "negative_review_rate"
    elif "average review" in lowered: intent = "average_review_score"
    elif "unique customer" in lowered: intent = "unique_customers"
    elif "average order value" in lowered or re.search(r"\baov\b", lowered): intent = "aov"
    elif "orders" in lowered: intent = "total_orders"
    elif "revenue" in lowered: intent = "total_revenue"
    else: raise UnsupportedQuestion("The question could not be mapped to an approved analytics intent.")
    plan = IntentPlan(intent=intent, limit=limit, states=states[:2] if intent == "compare_states" else (), start_date=start, end_date=end, interpretation=f"Approved intent: {intent.replace('_', ' ')}")
    return validate_plan_metadata(plan, text)


def _openai_compatible_content(settings, prompt, text):
    payload = json.dumps({"model": settings.model, "temperature": 0, "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}]}).encode()
    request = Request(settings.base_url + "/chat/completions", data=payload, headers={"Authorization": "Bearer " + settings.api_key, "Content-Type": "application/json"})
    with urlopen(request, timeout=25) as response:
        return json.loads(response.read())["choices"][0]["message"]["content"]


def _gemini_content(settings, prompt, text):
    schema = {
        "type": "OBJECT",
        "properties": {
            "intent": {"type": "STRING", "enum": sorted((*SUPPORTED_INTENTS, "unsupported"))},
            "limit": {"type": "INTEGER", "minimum": 1, "maximum": 25},
            "states": {"type": "ARRAY", "items": {"type": "STRING"}, "maxItems": 2},
            "categories": {"type": "ARRAY", "items": {"type": "STRING"}, "maxItems": 2},
            "start_date": {"type": "STRING", "description": "ISO date or empty string"},
            "end_date": {"type": "STRING", "description": "ISO date or empty string"},
            "interpretation": {"type": "STRING"},
            "metric": {"type": "STRING", "enum": ["total_revenue", "total_orders", "unique_customers", "aov", "delivery_rate", "late_delivery_rate", "average_review_score", "negative_review_rate", "merchandise_revenue", "payment_revenue", "orders", "payment_usage", "average_order_value", "average_delivery_days"]},
            "dimension": {"type": "STRING", "enum": ["scalar", "category", "state", "seller_id", "month", "payment_type"]},
            "chart_type": {"type": "STRING", "enum": ["kpi", "bar", "line", "donut", "table"]},
            "ranking_direction": {"type": "STRING", "enum": ["ascending", "descending", "none"]},
            "time_grain": {"type": "STRING", "enum": ["month", "none"]},
        },
        "required": ["intent", "limit", "states", "categories", "start_date", "end_date", "interpretation", "metric", "dimension", "chart_type", "ranking_direction", "time_grain"],
    }
    payload = json.dumps({
        "systemInstruction": {"parts": [{"text": prompt}]},
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 300, "responseMimeType": "application/json", "responseSchema": schema},
    }).encode()
    url = f"{settings.base_url}/models/{quote(settings.model, safe='')}:generateContent"
    request = Request(url, data=payload, headers={"x-goog-api-key": settings.api_key, "Content-Type": "application/json"})
    with urlopen(request, timeout=25) as response:
        result = json.loads(response.read())
    return result["candidates"][0]["content"]["parts"][0]["text"]


def provider_plan(question: str, active_filters=None) -> IntentPlan:
    settings = AISettings.from_environment()
    if settings is None:
        raise AssistantUnavailable("No governed AI provider is configured. Set AI_API_KEY and AI_MODEL to activate conversational planning.")
    text = precheck_question(question)
    active_scope = ""
    if active_filters is not None:
        active_scope = f"\nActive dashboard scope: date {active_filters.start_date} to {active_filters.end_date}; destination states {list(active_filters.states) or ['all']}; categories {list(active_filters.categories) or ['all']}. Explicit question scope overrides only the named dimension."
    prompt = semantic_prompt() + active_scope + "\nReturn only JSON with: intent, metric, dimension, chart_type, ranking_direction, time_grain, limit, states, categories, start_date, end_date, interpretation. Do not return SQL."
    try:
        content = _gemini_content(settings, prompt, text) if settings.provider == "gemini" else _openai_compatible_content(settings, prompt, text)
    except (HTTPError, URLError, TimeoutError, KeyError, ValueError) as exc:
        LOGGER.warning("Governed AI provider request failed (%s)", type(exc).__name__)
        raise AssistantUnavailable("The governed AI provider is temporarily unavailable. No database query was executed.")
    try:
        raw = json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
        intent = str(raw.get("intent", "unsupported"))
        if intent not in SUPPORTED_INTENTS:
            raise UnsupportedQuestion("The requested analysis is not supported by the approved semantic layer.")
        parse_date = lambda value: date.fromisoformat(value) if value else None
        states = tuple(str(value).strip().upper() for value in (raw.get("states") or ()) if str(value).strip().lower() not in {"", "all", "none"})[:2]
        categories = tuple(str(value).strip() for value in (raw.get("categories") or ()) if str(value).strip().lower() not in {"", "all", "none"})[:2]
        metadata = QueryMetadata(str(raw.get("metric", "")), str(raw.get("dimension", "")), str(raw.get("chart_type", "table")), str(raw.get("ranking_direction", "none")), None if raw.get("time_grain") in {None, "", "none"} else str(raw.get("time_grain")))
        plan = IntentPlan(intent, min(max(int(raw.get("limit", 10)), 1), 25), states, categories, parse_date(raw.get("start_date")), parse_date(raw.get("end_date")), str(raw.get("interpretation") or intent.replace("_", " ")), metadata)
        return validate_plan_metadata(plan, text)
    except (TypeError, ValueError, json.JSONDecodeError):
        raise UnsupportedQuestion("The provider did not return a valid approved query plan.")
