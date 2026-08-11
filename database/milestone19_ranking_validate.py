"""Live Gemini/PostgreSQL validation for ranking and chart semantics."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.assistant import ask_assistant
from streamlit_app.assistant.charting import build_answer_chart
from streamlit_app.services.common import get_filter_options
from streamlit_app.utils.filters import FilterState


CASES = (
    ("Show me the top 10 product categories by number of orders.", "orders", "category", "descending", "bar"),
    ("Show the top 10 product categories by merchandise revenue.", "merchandise_revenue", "category", "descending", "bar"),
    ("Show the 10 lowest performing product categories by merchandise revenue.", "merchandise_revenue", "category", "ascending", "bar"),
    ("Which 10 states have the most orders?", "orders", "state", "descending", "bar"),
    ("Show monthly revenue trend.", "payment_revenue", "month", "none", "line"),
    ("Which states have the highest late-delivery rate?", "late_delivery_rate", "state", "descending", "bar"),
)


def main():
    start, end, _, _ = get_filter_options()
    filters = FilterState(start, end)
    for question, metric, dimension, direction, chart_type in CASES:
        answer = ask_assistant(question, filters, use_llm=True)
        metadata = answer.metadata
        assert (metadata.metric, metadata.dimension, metadata.ranking_direction, metadata.chart_type) == (metric, dimension, direction, chart_type)
        assert metric in answer.data.columns and dimension in answer.data.columns
        if direction != "none":
            values = answer.data[metric].astype(float)
            assert values.is_monotonic_increasing if direction == "ascending" else values.is_monotonic_decreasing
            assert f"ORDER BY {metric} {'ASC' if direction == 'ascending' else 'DESC'}" in answer.sql
        else:
            assert answer.data[dimension].is_monotonic_increasing
        figure = build_answer_chart(answer)
        assert figure is not None
        if chart_type == "bar":
            assert figure.layout.xaxis.title.text
        else:
            assert figure.layout.yaxis.title.text == "Payment revenue"
        if direction == "ascending":
            assert "lowest" in answer.message.lower() and "leads" not in answer.message.lower()
        print({"intent": answer.intent, "metric": metric, "dimension": dimension, "direction": direction, "rows": len(answer.data), "scope": answer.scope})


if __name__ == "__main__":
    main()
