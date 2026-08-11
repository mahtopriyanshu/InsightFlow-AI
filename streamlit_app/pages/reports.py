"""Reports and downloads page."""
from io import BytesIO

import pandas as pd
import streamlit as st

from streamlit_app.components.layout import dataframe_panel, filter_context, page_header, report_card, section_header
from streamlit_app.services.reports import get_report_dataset
from streamlit_app.utils.filters import FilterState


def _excel_bytes(dataframe: pd.DataFrame, sheet_name: str) -> bytes:
    """Serialize a DataFrame to a clean in-memory Excel workbook."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    return buffer.getvalue()


def render(filters: FilterState) -> None:
    """Render filtered previews and CSV/Excel downloads."""
    page_header(
        "Reports",
        "Create portable, filter-aware extracts for deeper analysis and sharing.",
        "Data Exports",
    )
    filter_context(filters.start_date, filters.end_date, filters.states, filters.categories)
    descriptions = {
        "Order performance": "Order status, revenue, freight, and delivery outcomes.",
        "Customer summary": "Customer value, order frequency, location, and lifecycle dates.",
        "Seller performance": "Seller revenue, volume, inventory movement, and geography.",
        "Category performance": "Category revenue, demand, items sold, and freight economics.",
    }
    section_header("Report library", "Filter-aware datasets with a controlled 50,000-row safety limit.")
    cards = st.columns(4)
    for index, (column, (name, description)) in enumerate(zip(cards, descriptions.items())):
        with column:
            report_card(name, description)
            if st.button("Select report", key=f"select_report_{index}", use_container_width=True):
                st.session_state["selected_report"] = name
    report_name = st.selectbox(
        "Report dataset",
        list(descriptions),
        index=list(descriptions).index(st.session_state.get("selected_report", "Order performance")),
    )
    row_limit = st.select_slider(
        "Maximum rows",
        options=[1_000, 5_000, 10_000, 25_000, 50_000],
        value=10_000,
    )
    with st.spinner(f"Preparing {report_name.lower()}..."):
        dataframe = get_report_dataset(report_name, filters, row_limit)

    section_header("Generation workspace", f"{report_name} · {row_limit:,} row limit · CSV and Excel available")
    st.caption(f"{len(dataframe):,} rows prepared using the active global filters.")
    dataframe_panel(dataframe.head(1_000), height=500)

    safe_name = report_name.lower().replace(" ", "_")
    columns = st.columns(2)
    with columns[0]:
        st.download_button(
            "Download CSV",
            data=dataframe.to_csv(index=False).encode("utf-8"),
            file_name=f"insightflow_{safe_name}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with columns[1]:
        st.download_button(
            "Download Excel",
            data=_excel_bytes(dataframe, report_name),
            file_name=f"insightflow_{safe_name}.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

    st.info(
        "Exports reflect the current date, state, and category filters. "
        "PDF generation is intentionally deferred until a governed report "
        "template is approved.",
        icon="💡",
    )
