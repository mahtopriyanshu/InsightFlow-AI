"""Headless interaction validation for the Compare & Explain workspace."""
from pathlib import Path
from datetime import date
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
def main():
    app=AppTest.from_file(str(ROOT/"streamlit_app"/"app.py"),default_timeout=240).run()
    sales=next(x for x in app.sidebar.radio[0].options if "Sales Analytics" in x)
    app.sidebar.radio[0].set_value(sales).run(timeout=240)
    app.sidebar.date_input[0].set_value((date(2018,1,1),date(2018,3,31))).run(timeout=240)
    toggle=next(x for x in app.toggle if x.label=="Enable interactive Compare Mode")
    toggle.set_value(True).run(timeout=240)
    assert not app.exception and not app.error
    modes=["Period vs Period","Category vs Category","Destination State vs State","Seller vs Seller"]
    for mode in modes:
        selector=next(x for x in app.selectbox if x.label=="Compare type")
        selector.set_value(mode).run(timeout=240)
        assert not app.exception and not app.error
        assert any("Key differences" in str(x.value) for x in app.markdown)
        print(mode,{"plotly":len(app.get("plotly_chart")),"expanders":len(app.expander)})
    assert any("What contributed to the change" in str(x.value) for x in app.markdown)
    print("compare_explain_ui=passed")
if __name__=="__main__":main()
