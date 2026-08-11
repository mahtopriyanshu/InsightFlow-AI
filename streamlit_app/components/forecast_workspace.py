"""Premium opt-in presentation for validated M18 forecasts."""
import logging
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from streamlit_app.components.layout import dataframe_panel, kpi_card, section_header
from streamlit_app.forecasting import build_forecast
from streamlit_app.styles.theme import COLORS
from streamlit_app.utils.formatting import currency, number, percentage

LOGGER = logging.getLogger(__name__)


def _format(value, unit):
    return currency(value) if unit == "currency" else number(value)


def _chart(target):
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=target.history.month, y=target.history[target.target], name="Historical actual", mode="lines+markers", line={"color": COLORS["purple"], "width": 3}))
    figure.add_trace(go.Scatter(x=target.backtest.month, y=target.backtest.predicted, name="Walk-forward prediction", mode="lines+markers", line={"color": COLORS["blue"], "width": 2, "dash": "dot"}))
    future = pd.DataFrame([point.__dict__ for point in target.future])
    if future.lower.notna().all():
        figure.add_trace(go.Scatter(x=future.period, y=future.upper, mode="lines", line={"width": 0}, hoverinfo="skip", showlegend=False))
        figure.add_trace(go.Scatter(x=future.period, y=future.lower, mode="lines", fill="tonexty", fillcolor="rgba(59,130,246,.14)", line={"width": 0}, name="Approx. 90% residual band", hovertemplate="Lower %{y:,.2f}<extra></extra>"))
    figure.add_trace(go.Scatter(x=future.period, y=future.value, name="Future forecast", mode="lines+markers", line={"color": COLORS["cyan"], "width": 3, "dash": "dash"}))
    prefix = "R$ " if target.unit == "currency" else ""
    figure.update_layout(title=f"{target.target.title()}: actual, backtest, and forecast", height=390, paper_bgcolor=COLORS["card"], plot_bgcolor=COLORS["card"], margin={"l": 24, "r": 20, "t": 58, "b": 24}, font={"family": "Inter", "color": COLORS["muted"]}, hovermode="x unified", legend_title_text="")
    figure.update_xaxes(showgrid=False, linecolor=COLORS["border"])
    figure.update_yaxes(gridcolor=COLORS["border"], tickprefix=prefix, tickformat=",.0f")
    return figure


def _target_panel(target):
    best = target.scores[0]
    columns = st.columns(4)
    with columns[0]:
        kpi_card("Next month forecast", _format(target.future[0].value, target.unit), note="Model estimate, not an actual")
    with columns[1]:
        kpi_card("Selected model", target.selected_model, note="Lowest walk-forward WAPE")
    with columns[2]:
        kpi_card("Validation WAPE", percentage(best.wape), note=f"{best.observations} forecast origins")
    with columns[3]:
        kpi_card("Forecast horizon", f"{len(target.future)} months", note="Conservative near-term horizon")
    st.plotly_chart(_chart(target), use_container_width=True)
    table = pd.DataFrame([{
        "Model": score.model,
        "MAE": score.mae,
        "RMSE": score.rmse,
        "WAPE (%)": score.wape,
        "Backtest origins": score.observations,
        "Selected": "Yes" if score.selected else "",
    } for score in target.scores])
    dataframe_panel(table, height=245)
    with st.expander("Why this model and how is uncertainty calculated?"):
        st.markdown(f"**Selection:** {target.rationale}\n\n**Validation:** expanding-window one-month-ahead backtesting; no random train/test split.\n\n**Uncertainty:** the displayed approximate 90% band adds and subtracts the selected model's 90th percentile absolute walk-forward residual. It summarizes observed validation error and is not a guarantee or a native probabilistic interval.")


def render_forecast_workspace(filters):
    section_header("Validated Forecasting", "Near-term payment-revenue and distinct-order forecasts selected by chronological backtesting.")
    if not st.toggle("Enable validated forecasting", value=False, key="enable_validated_forecasting"):
        st.caption("Enable to load cached historical series, five candidate models, and walk-forward validation results.")
        return
    try:
        with st.spinner("Validating candidate forecast models..."):
            report = build_forecast(filters)
    except Exception as exc:
        LOGGER.error("Forecast service failed (%s)", type(exc).__name__)
        st.warning("Forecasting is temporarily unavailable. The rest of Sales Analytics remains available.")
        return
    st.caption(f"Scope: {report.scope} · Complete monthly periods: {report.complete_periods} · Forecast horizon: {report.horizon} months")
    if report.unavailable_reason:
        st.warning(report.unavailable_reason)
        return
    revenue_tab, orders_tab = st.tabs(["Revenue Forecast", "Orders Forecast"])
    with revenue_tab:
        _target_panel(report.revenue)
    with orders_tab:
        _target_panel(report.orders)
