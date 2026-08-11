"""Headless interaction validation for the opt-in M18 Sales workspace."""
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def main():
    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"), default_timeout=180).run()
    sales = next(page for page in app.sidebar.radio[0].options if "Sales Analytics" in page)
    app.sidebar.radio[0].set_value(sales).run(timeout=180)
    toggle = next(item for item in app.toggle if item.label == "Enable validated forecasting")
    toggle.set_value(True).run(timeout=180)
    assert not app.exception, [str(item.value) for item in app.exception]
    assert not app.error, [str(item.value) for item in app.error]
    assert any("Next month forecast" in str(item.value) for item in app.markdown)
    assert len(app.get("plotly_chart")) >= 9
    assert len(app.dataframe) >= 3
    print({"forecast_ui": "passed", "plotly_charts": len(app.get("plotly_chart")), "dataframes": len(app.dataframe), "exceptions": 0})


if __name__ == "__main__":
    main()
