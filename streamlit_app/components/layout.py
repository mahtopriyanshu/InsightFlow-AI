"""Reusable product UI components."""
import html
from datetime import date

import streamlit as st

from streamlit_app.insights.models import Insight
from streamlit_app.anomalies.models import Alert


def page_header(title: str, description: str, eyebrow: str = "InsightFlow AI") -> None:
    """Render a consistent page heading."""
    st.markdown(
        f'<div class="if-eyebrow">{html.escape(eyebrow)}</div>'
        f'<div class="if-page-title">{html.escape(title)}</div>'
        f'<div class="if-page-copy">{html.escape(description)}</div>',
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, icon: str = "◈", note: str = "Live filtered data") -> None:
    """Render a polished KPI card."""
    st.markdown(
        f'<div class="if-kpi"><div class="if-kpi-top"><span class="if-kpi-icon">{html.escape(icon)}</span>'
        f'<span class="if-kpi-label">{html.escape(label)}</span></div>'
        f'<div class="if-kpi-value">{html.escape(value)}</div>'
        f'<div class="if-kpi-footer"><span class="if-kpi-accent"></span>{html.escape(note)}</div></div>',
        unsafe_allow_html=True,
    )


def insight_card(title: str, message: str, icon: str = "✦", *,
                 severity: str = "informational",
                 supporting_label: str | None = None) -> None:
    """Render a deterministic business insight."""
    metric_html = (
        f'<div class="if-insight-metric">{html.escape(supporting_label)}</div>'
        if supporting_label else ""
    )
    st.markdown(
        f'<div class="if-insight {html.escape(severity)}"><div class="if-insight-icon">{html.escape(icon)}</div><div><div class="if-insight-title">'
        f'{html.escape(title)}</div><div class="if-insight-copy">'
        f'{html.escape(message)}</div>{metric_html}'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def render_insights(insights: list[Insight], *, columns: int = 4) -> None:
    """Render structured insights and compact expandable evidence."""
    if not insights:
        st.info(
            "No reliable insight met the comparison or sample-size guardrails "
            "for the selected filters.", icon="ℹ️",
        )
        return
    containers = st.columns(min(columns, len(insights)))
    for index, insight in enumerate(insights):
        with containers[index % len(containers)]:
            insight_card(
                insight.title, insight.message, insight.icon,
                severity=insight.severity,
                supporting_label=insight.supporting_label,
            )
            if insight.evidence:
                with st.expander("View evidence", expanded=False):
                    evidence = insight.evidence
                    rows = [
                        ("Current", evidence.current_value),
                        ("Previous", evidence.previous_value),
                        ("Difference", evidence.difference),
                        ("Period", evidence.period),
                        ("Comparison", evidence.comparison_period),
                        ("Sample", f"{evidence.sample_size:,}" if evidence.sample_size is not None else None),
                        ("Scope", insight.scope),
                        ("Source", evidence.source),
                    ]
                    st.markdown("\n".join(
                        f"**{label}:** {value}" for label, value in rows if value
                    ))


def render_alerts(alerts: list[Alert], *, columns: int = 3) -> None:
    """Render prioritized statistical alerts with transparent detector evidence."""
    if not alerts:
        st.info("No unusual movement met the history, magnitude, sample, and robust-variation guardrails in the selected scope.",icon="ℹ️")
        return
    containers=st.columns(min(columns,len(alerts)))
    for index,alert in enumerate(alerts):
        with containers[index%len(containers)]:
            icon="▲" if alert.category=="opportunity" else "!"
            insight_card(alert.title,alert.message,icon,severity=alert.severity,supporting_label=alert.evidence.deviation)
            with st.expander("Why was this flagged?",expanded=False):
                evidence=alert.evidence
                st.markdown("\n".join([
                    f"**Observed:** {evidence.observed}",f"**Historical baseline:** {evidence.baseline}",
                    f"**Deviation:** {evidence.deviation}",f"**Period / entity:** {alert.period} · {alert.entity_label}",
                    f"**Method:** {evidence.detector_method}",f"**Historical periods:** {evidence.historical_periods}",
                    f"**Threshold:** {evidence.threshold}",f"**Sample:** {evidence.sample_size:,}" if evidence.sample_size is not None else "",
                    f"**Scope:** {alert.scope}",
                ]))


def section_header(title: str, description: str = "") -> None:
    """Render a compact section introduction."""
    st.markdown(
        f'<div class="if-section-title">{html.escape(title)}</div>'
        f'<div class="if-section-copy">{html.escape(description)}</div>',
        unsafe_allow_html=True,
    )


def status_badge(label: str, tone: str = "success") -> None:
    """Render a semantic status chip."""
    safe_tone = tone if tone in {"success", "warning", "danger", "info"} else "info"
    st.markdown(f'<span class="if-badge {safe_tone}">{html.escape(label)}</span>', unsafe_allow_html=True)


def health_indicator(label: str, value: float, display: str, help_text: str, *, inverse: bool = False) -> None:
    """Render a data-backed compact gauge/progress indicator."""
    raw = max(0.0, min(100.0, float(value or 0)))
    score = 100.0 - raw if inverse else raw
    tone = "success" if score >= 80 else "warning" if score >= 60 else "danger"
    st.markdown(
        f'<div class="if-health"><div class="if-health-row"><div><div class="if-health-label">{html.escape(label)}</div>'
        f'<div class="if-health-help">{html.escape(help_text)}</div></div><span class="if-badge {tone}">{html.escape(display)}</span></div>'
        f'<div class="if-progress"><span class="{tone}" style="width:{score:.1f}%"></span></div></div>', unsafe_allow_html=True)


def filter_context(start_date: date, end_date: date, states: tuple[str, ...], categories: tuple[str, ...]) -> None:
    """Show active analytics context without exposing implementation details."""
    state_label = f"{len(states)} states" if states else "All states"
    category_label = f"{len(categories)} categories" if categories else "All categories"
    st.markdown(
        f'<div class="if-context"><span>📅 {start_date:%d %b %Y} – {end_date:%d %b %Y}</span>'
        f'<span>📍 {state_label}</span><span>▦ {category_label}</span></div>', unsafe_allow_html=True)


def ranking_list(dataframe, label_col: str, value_col: str, formatter, limit: int = 5) -> None:
    """Render a visual ranked list from actual analytical results."""
    if dataframe.empty:
        empty_state("No ranking data matches the current filters.")
        return
    maximum = max(float(dataframe[value_col].astype(float).max()), 1.0)
    rows = []
    for rank, (_, row) in enumerate(dataframe.head(limit).iterrows(), 1):
        width = 100 * float(row[value_col]) / maximum
        rows.append(f'<div class="if-rank"><span class="if-rank-num">{rank:02}</span><div class="if-rank-main"><div class="if-rank-row"><b>{html.escape(str(row[label_col]))}</b><span>{html.escape(formatter(row[value_col]))}</span></div><div class="if-rank-bar"><span style="width:{width:.1f}%"></span></div></div></div>')
    st.markdown('<div class="if-ranking">' + ''.join(rows) + '</div>', unsafe_allow_html=True)


def report_card(title: str, description: str, formats: str = "CSV · XLSX") -> None:
    st.markdown(f'<div class="if-report"><div class="if-report-icon">↧</div><div><div class="if-report-title">{html.escape(title)}</div><div class="if-report-copy">{html.escape(description)}</div><span class="if-badge info">{html.escape(formats)}</span></div></div>', unsafe_allow_html=True)


def profile_card(title: str, identifier: str, fields: list[tuple[str, str]], icon: str = "◉") -> None:
    """Render a polished search-result profile summary."""
    stats = "".join(
        f'<div class="if-profile-stat"><span>{html.escape(label)}</span><b>{html.escape(value)}</b></div>'
        for label, value in fields
    )
    st.markdown(
        f'<div class="if-profile"><div class="if-profile-head"><div class="if-profile-avatar">{html.escape(icon)}</div>'
        f'<div><div class="if-profile-label">SELECTED PROFILE</div><div class="if-profile-title">{html.escape(title)}</div>'
        f'<div class="if-profile-id">{html.escape(identifier)}</div></div></div><div class="if-profile-grid">{stats}</div></div>',
        unsafe_allow_html=True,
    )


def empty_state(message: str) -> None:
    """Render a friendly empty-data state."""
    st.info(message, icon="ℹ️")


def dataframe_panel(dataframe, *, height: int = 420) -> None:
    """Render a responsive analytical table."""
    if dataframe.empty:
        empty_state("No records match the current filters.")
        return
    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
        height=height,
    )
