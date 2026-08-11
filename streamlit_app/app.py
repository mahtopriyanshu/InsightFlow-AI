"""InsightFlow AI — E-Commerce Intelligence Platform."""
import logging
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOGGER = logging.getLogger(__name__)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from streamlit_app.database.connection import healthcheck
from streamlit_app.pages import (
    assistant,
    customers,
    delivery,
    overview,
    products,
    reports,
    reviews,
    sales,
    sellers,
)
from streamlit_app.services.common import get_filter_options
from streamlit_app.styles.theme import apply_theme
from streamlit_app.utils.filters import FilterState

st.set_page_config(
    page_title="InsightFlow AI",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

PAGES = {
    "⌂  Executive Overview": overview.render,
    "▥  Sales Analytics": sales.render,
    "♙  Customer Intelligence": customers.render,
    "▣  Product Intelligence": products.render,
    "♧  Seller Intelligence": sellers.render,
    "🚚  Delivery Analytics": delivery.render,
    "★  Review Analytics": reviews.render,
    "▧  Reports": reports.render,
    "✦  AI Assistant": assistant.render,
}


def _brand() -> None:
    st.sidebar.markdown(
        """
        <div class="if-brand">
            <div class="if-brand-mark">▣</div>
            <div><div class="if-brand-title">InsightFlow AI</div>
            <div class="if-brand-subtitle">E-Commerce Intelligence Platform</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _global_filters() -> FilterState:
    """Render persistent global filters and return immutable state."""
    min_date, max_date, states, categories = get_filter_options()
    st.sidebar.markdown('<div class="if-nav-label">GLOBAL FILTERS</div>', unsafe_allow_html=True)
    date_range = st.sidebar.date_input(
        "Order Date",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="global_date_range",
    )
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range[0]

    selected_states = st.sidebar.multiselect(
        "Customer state",
        options=states,
        key="global_states",
        placeholder="All states",
    )
    selected_categories = st.sidebar.multiselect(
        "Product category",
        options=categories,
        key="global_categories",
        placeholder="All categories",
    )
    if st.sidebar.button("↺  Reset filters", use_container_width=True):
        for key in ("global_date_range", "global_states", "global_categories"):
            st.session_state.pop(key, None)
        st.cache_data.clear()
        st.rerun()

    return FilterState(
        start_date=start_date,
        end_date=end_date,
        states=tuple(selected_states),
        categories=tuple(selected_categories),
    )


def main() -> None:
    """Run the product shell and selected analytics page."""
    _brand()
    healthy, detail = healthcheck()
    if not healthy:
        st.error(
            "InsightFlow AI could not connect to PostgreSQL. "
            "Confirm the DB_* environment variables and that PostgreSQL is running.",
            icon="🚨",
        )
        st.stop()

    st.sidebar.markdown('<div class="if-nav-label">WORKSPACE</div>', unsafe_allow_html=True)
    selected_page = st.sidebar.radio(
        "Workspace",
        options=list(PAGES),
        label_visibility="collapsed",
    )
    try:
        filters = _global_filters()
        PAGES[selected_page](filters)
    except Exception as exc:
        LOGGER.error("Application page failed (%s)", type(exc).__name__)
        st.error(
            "This view could not be loaded. Your database was not modified. Please retry or review the application logs.",
            icon="⚠️",
        )
        with st.expander("Troubleshooting"):
            st.code('1. Confirm all Milestone 6 views exist.\n2. Verify the ETL load completed.\n3. Refresh cached data from the Streamlit menu.')
    finally:
        st.sidebar.markdown("---")
        st.sidebar.markdown(
            f'<div class="if-db"><span class="if-db-dot"></span><div><b>PostgreSQL Connected</b><small>{detail}</small></div></div>',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()



