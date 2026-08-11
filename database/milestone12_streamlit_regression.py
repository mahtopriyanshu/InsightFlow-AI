"""Headless nine-page Streamlit regression for Milestone 12."""
from pathlib import Path
from time import perf_counter
import sys

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.services.common import get_filter_options
from streamlit_app.services.customers import get_top_customers
from streamlit_app.services.portfolio import get_product_analytics, get_seller_analytics
from streamlit_app.utils.filters import FilterState

def main() -> None:
    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"), default_timeout=90)
    started = perf_counter()
    app.run()
    pages = list(app.sidebar.radio[0].options)
    results = {}
    for page in pages:
        page_start = perf_counter()
        app.sidebar.radio[0].set_value(page).run(timeout=90)
        assert not app.exception, f"{page}: {[str(item.value) for item in app.exception]}"
        assert not app.error, f"{page}: {[str(item.value) for item in app.error]}"
        safe_page = page.encode("ascii", "ignore").decode().strip()
        results[safe_page] = {
            "seconds": round(perf_counter() - page_start, 3),
            "plotly_charts": len(app.get("plotly_chart")),
            "dataframes": len(app.dataframe),
            "download_buttons": len(app.get("download_button")),
        }
    assert any("Customer Intelligence" in page for page in pages)
    assert any("AI Assistant" in page for page in pages)
    customer_page = next(page for page in pages if "Customer Intelligence" in page)
    start_date, end_date, _, _ = get_filter_options()
    customer_id = str(get_top_customers(FilterState(start_date, end_date), 1).iloc[0]["customer_unique_id"])
    app.sidebar.radio[0].set_value(customer_page).run(timeout=90)
    app.text_input[0].set_value(customer_id[:8]).run(timeout=90)
    assert not app.exception
    assert app.selectbox and customer_id in app.selectbox[0].options
    results["Customer search interaction"] = {"matches": len(app.selectbox[0].options), "passed": True}
    filters=FilterState(start_date,end_date)
    product_page=next(page for page in pages if "Product Intelligence" in page)
    product_id=str(get_product_analytics(filters).iloc[0]["product_id"])
    app.sidebar.radio[0].set_value(product_page).run(timeout=90)
    app.text_input[0].set_value(product_id[:8]).run(timeout=90)
    assert not app.exception and not app.error and product_id in app.selectbox[0].options
    results["Product search interaction"]={"matches":len(app.selectbox[0].options),"passed":True}
    seller_page=next(page for page in pages if "Seller Intelligence" in page)
    seller_id=str(get_seller_analytics(filters).iloc[0]["seller_id"])
    app.sidebar.radio[0].set_value(seller_page).run(timeout=90)
    app.text_input[0].set_value(seller_id[:8]).run(timeout=90)
    assert not app.exception and not app.error and seller_id in app.selectbox[-1].options
    results["Seller search interaction"]={"matches":len(app.selectbox[-1].options),"passed":True}
    print("pages", results)
    print("total_seconds", round(perf_counter() - started, 3))


if __name__ == "__main__":
    main()
