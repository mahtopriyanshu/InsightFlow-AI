"""Consistent interactive Plotly chart factories."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from streamlit_app.styles.theme import COLORS


def _style(figure: go.Figure, title: str) -> go.Figure:
    figure.update_layout(
        title={"text": title, "font": {"size": 16, "color": COLORS["navy"]}},
        paper_bgcolor=COLORS["card"],
        plot_bgcolor=COLORS["card"],
        font={"family": "Inter", "color": COLORS["muted"]},
        margin={"l": 24, "r": 20, "t": 58, "b": 24},
        hoverlabel={"bgcolor": COLORS["navy"], "font_color": "white"},
        legend_title_text="",
        hovermode="x unified" if len(figure.data) > 1 else "closest",
        height=350,
        modebar={"remove": ["lasso2d", "select2d"]},
    )
    figure.update_xaxes(showgrid=False, linecolor=COLORS["border"])
    figure.update_yaxes(gridcolor=COLORS["border"], zeroline=False)
    return figure


def trend_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    y_title: str = "",
) -> go.Figure:
    figure = px.line(
        data,
        x=x,
        y=y,
        markers=True,
        color_discrete_sequence=[COLORS["purple"]],
    )
    figure.update_traces(line_width=3, marker_size=7)
    if "revenue" in y.lower() or "value" in y.lower():
        figure.update_traces(hovertemplate="%{x|%b %Y}<br><b>R$ %{y:,.2f}</b><extra></extra>")
        figure.update_yaxes(tickprefix="R$ ", tickformat=",.0f")
    else:
        figure.update_traces(hovertemplate="%{x|%b %Y}<br><b>%{y:,.2f}</b><extra></extra>")
    figure.update_yaxes(title=y_title)
    return _style(figure, title)


def multi_trend_chart(
    data: pd.DataFrame,
    x: str,
    columns: list[str],
    title: str,
) -> go.Figure:
    figure = go.Figure()
    palette = [COLORS["purple"], COLORS["blue"], COLORS["cyan"]]
    for index, column in enumerate(columns):
        figure.add_trace(
            go.Scatter(
                x=data[x],
                y=data[column],
                name=column.replace("_", " ").title(),
                mode="lines+markers",
                line={"width": 3, "color": palette[index % len(palette)]},
            )
        )
    return _style(figure, title)


def performance_trends(data: pd.DataFrame) -> go.Figure:
    """Create a readable dual-axis revenue/orders/AOV performance view."""
    figure = go.Figure()
    figure.add_trace(go.Bar(x=data["month"], y=data["revenue"], name="Revenue", opacity=.78, marker_color=COLORS["purple"], hovertemplate="R$ %{y:,.2f}<extra>Revenue</extra>"))
    figure.add_trace(go.Scatter(x=data["month"], y=data["average_order_value"], name="AOV", mode="lines+markers", line={"width": 2, "color": COLORS["cyan"]}, hovertemplate="R$ %{y:,.2f}<extra>AOV</extra>"))
    figure.add_trace(go.Scatter(x=data["month"], y=data["orders"], name="Orders", mode="lines+markers", line={"width":2,"color":COLORS["blue"]}, yaxis="y2", hovertemplate="%{y:,.0f}<extra>Orders</extra>"))
    figure.update_layout(yaxis={"title": "Revenue / AOV", "tickprefix": "R$ "}, yaxis2={"title": "Orders", "overlaying": "y", "side": "right", "showgrid": False})
    return _style(figure, "Commercial performance trends")


def bar_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    *,
    horizontal: bool = False,
    color: str | None = None,
) -> go.Figure:
    figure = px.bar(
        data,
        x=y if horizontal else x,
        y=x if horizontal else y,
        orientation="h" if horizontal else "v",
        color=color,
        color_discrete_sequence=[
            COLORS["purple"], COLORS["blue"], COLORS["cyan"],
            COLORS["warning"], COLORS["negative"],
        ],
    )
    return _style(figure, title)


def distribution_chart(
    data: pd.DataFrame,
    names: str,
    values: str,
    title: str,
) -> go.Figure:
    figure = px.pie(
        data,
        names=names,
        values=values,
        hole=0.58,
        color_discrete_sequence=[
            COLORS["purple"], COLORS["blue"], COLORS["cyan"],
            COLORS["warning"], COLORS["negative"],
        ],
    )
    figure.update_traces(textposition="inside", textinfo="percent+label")
    return _style(figure, title)


def status_donut(data: pd.DataFrame, names: str, values: str, title: str, color_map: dict[str, str]) -> go.Figure:
    """Create a semantic-color donut for operational status data."""
    labels = data[names].astype(str).tolist()
    figure = go.Figure(go.Pie(labels=labels, values=data[values], hole=.62,
        marker={"colors": [color_map.get(label, COLORS["muted"]) for label in labels]},
        textinfo="percent", hovertemplate="%{label}<br><b>%{value:,.0f}</b> (%{percent})<extra></extra>"))
    return _style(figure, title)


def histogram_chart(
    data: pd.DataFrame,
    x: str,
    title: str,
    bins: int = 30,
) -> go.Figure:
    figure = px.histogram(
        data,
        x=x,
        nbins=bins,
        color_discrete_sequence=[COLORS["purple"]],
    )
    return _style(figure, title)


def scatter_chart(data: pd.DataFrame, x: str, y: str, title: str, *, size: str | None = None, color: str | None = None) -> go.Figure:
    """Create a compact interactive performance matrix."""
    plot_data = data.copy()
    for column in (x, y, size):
        if column:
            plot_data[column] = pd.to_numeric(plot_data[column], errors="coerce").astype(float)
    figure = px.scatter(plot_data, x=x, y=y, size=size, color=color,
        color_discrete_sequence=[COLORS["purple"], COLORS["blue"], COLORS["cyan"]],
        hover_data=plot_data.columns.tolist())
    figure.update_traces(marker={"opacity": .78, "line": {"width": 1, "color": "white"}})
    return _style(figure, title)


def rfm_segment_donut(data: pd.DataFrame, values: str, title: str,
                      color_map: dict[str, str]) -> go.Figure:
    """Create an RFM donut with stable segment colors across measures."""
    labels = data["segment"].astype(str).tolist()
    figure = go.Figure(go.Pie(
        labels=labels, values=data[values], hole=.6,
        marker={"colors": [color_map[label] for label in labels]},
        textinfo="percent", hovertemplate="%{label}<br><b>%{value:,.2f}</b> (%{percent})<extra></extra>",
    ))
    return _style(figure, title)


def pareto_chart(data: pd.DataFrame, title: str) -> go.Figure:
    """Plot cumulative customer share against cumulative revenue share."""
    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=data["customer_share"], y=data["revenue_share"], mode="lines",
        line={"width": 3, "color": COLORS["purple"]}, name="Observed concentration",
        hovertemplate="Customers: %{x:.1f}%<br>Revenue: %{y:.1f}%<extra></extra>",
    ))
    figure.add_trace(go.Scatter(
        x=[0, 100], y=[0, 100], mode="lines", name="Equal distribution",
        line={"width": 1, "dash": "dash", "color": COLORS["muted"]}, hoverinfo="skip",
    ))
    figure.add_hline(y=80, line_dash="dot", line_color=COLORS["warning"])
    figure.update_xaxes(title="Cumulative customer share", ticksuffix="%", range=[0, 100])
    figure.update_yaxes(title="Cumulative revenue share", ticksuffix="%", range=[0, 100])
    return _style(figure, title)
