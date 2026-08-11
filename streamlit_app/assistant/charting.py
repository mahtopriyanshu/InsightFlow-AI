"""Deterministic charts driven only by validated query metadata."""
import hashlib

import plotly.express as px
import streamlit as st

from streamlit_app.assistant.presentation import humanize_entity, humanize_label
from streamlit_app.assistant.semantic import METRICS
from streamlit_app.styles.theme import COLORS


def assistant_element_key(answer, message_instance: str, element: str) -> str:
    """Create a stable non-secret key unique to one response instance."""
    metadata = answer.metadata
    source = "|".join((str(message_instance), element, answer.intent, metadata.chart_type, metadata.metric, metadata.dimension, metadata.ranking_direction, metadata.time_grain or "none", answer.question))
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:24]
    return f"assistant_{element}_{digest}"


def _chart_title(metadata) -> str:
    metric_label = METRICS[metadata.metric].label
    trend_label = {"orders": "Order", "unique_customers": "Unique Customer"}.get(metadata.metric, metric_label)
    if metadata.chart_type == "line": return f"Monthly {trend_label} Trend"
    if metadata.dimension == "state": return f"{metric_label} by State"
    if metadata.dimension == "category": return f"Product Categories by {metric_label}"
    if metadata.dimension == "seller_id": return f"Sellers by {metric_label}"
    return f"{metric_label} by {humanize_label(metadata.dimension)}"


def build_answer_chart(answer):
    data = answer.data; metadata = answer.metadata; kind = metadata.chart_type
    if kind in {"kpi", "table"} or len(data) == 1:
        return None
    if metadata.metric not in data.columns or metadata.dimension not in data.columns:
        raise ValueError("Verified chart metadata does not match the result columns.")
    metric_label = METRICS[metadata.metric].label
    dimension_label = humanize_label(metadata.dimension)
    plot_data = data.copy()
    if metadata.dimension in {"category", "payment_type"}:
        plot_data[metadata.dimension] = plot_data[metadata.dimension].map(humanize_entity)
    elif metadata.dimension == "seller_id":
        plot_data[metadata.dimension] = plot_data[metadata.dimension].map(lambda value: f"{str(value)[:10]}…" if len(str(value)) > 12 else str(value))
    if kind == "line":
        plot_data = plot_data.sort_values(metadata.dimension)
        figure = px.line(plot_data, x=metadata.dimension, y=metadata.metric, markers=True, labels={metadata.dimension: dimension_label, metadata.metric: metric_label}, color_discrete_sequence=[COLORS["purple"]])
    elif kind == "donut":
        figure = px.pie(plot_data, names=metadata.dimension, values=metadata.metric, hole=.58, labels={metadata.dimension: dimension_label, metadata.metric: metric_label}, color_discrete_sequence=[COLORS["purple"], COLORS["blue"], COLORS["cyan"], COLORS["warning"]])
    elif kind == "bar":
        # SQL already applies the validated ranking direction. Reverse only so
        # the first requested row appears at the top of a horizontal chart.
        plot_data = plot_data.iloc[::-1]
        figure = px.bar(plot_data, x=metadata.metric, y=metadata.dimension, orientation="h", labels={metadata.dimension: dimension_label, metadata.metric: metric_label}, color_discrete_sequence=[COLORS["purple"]])
    else:
        return None
    figure.update_layout(title={"text": _chart_title(metadata), "x": .01, "xanchor": "left", "font": {"size": 15, "color": "#0F172A"}}, showlegend=kind == "donut", height=360, paper_bgcolor=COLORS["card"], plot_bgcolor=COLORS["card"], margin={"l":24,"r":20,"t":54,"b":24}, font={"family":"Inter","color":COLORS["muted"]}, hoverlabel={"bgcolor":COLORS["navy"],"font_color":"white"})
    if metadata.metric in {"payment_revenue", "merchandise_revenue", "average_order_value"}: figure.update_xaxes(tickprefix="R$ ") if kind == "bar" else figure.update_yaxes(tickprefix="R$ ")
    elif metadata.metric in {"delivery_rate", "late_delivery_rate", "negative_review_rate"}: figure.update_xaxes(ticksuffix="%") if kind == "bar" else figure.update_yaxes(ticksuffix="%")
    elif metadata.metric == "average_delivery_days": figure.update_yaxes(ticksuffix=" days")
    return figure


def render_answer_chart(answer, message_instance: str):
    figure = build_answer_chart(answer)
    if figure is not None:
        st.plotly_chart(figure, use_container_width=True, key=assistant_element_key(answer, message_instance, "chart"))
