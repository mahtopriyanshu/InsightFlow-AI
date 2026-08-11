"""Governed AI Business Analyst conversational page."""
import streamlit as st

from streamlit_app.assistant import AISettings, AssistantError, ask_assistant
from streamlit_app.assistant.charting import assistant_element_key, render_answer_chart
from streamlit_app.assistant.history import append_message, clear_conversation_state
from streamlit_app.assistant.presentation import friendly_status, humanize_label, prepare_display_table
from streamlit_app.components.layout import filter_context, page_header, status_badge

SUGGESTED_QUESTIONS = (
    "Show the monthly revenue trend.",
    "Show the monthly order trend.",
    "Which states have the highest late-delivery rate?",
    "Show the top 10 categories by merchandise revenue.",
    "Show the monthly trend of unique customers.",
    "Compare SP and RJ by revenue.",
)


def _table_config(answer):
    config = {}
    for raw in answer.data.columns:
        label = humanize_label(raw)
        if raw == "month": config[label] = st.column_config.DateColumn(label, format="MMM YYYY")
        elif raw in {"payment_revenue", "merchandise_revenue", "payment_value", "average_order_value"}: config[label] = st.column_config.NumberColumn(label, format="R$ %.2f")
        elif raw in {"delivery_rate", "late_delivery_rate", "negative_review_rate"}: config[label] = st.column_config.NumberColumn(label, format="%.2f%%")
        elif raw == "average_delivery_days": config[label] = st.column_config.NumberColumn(label, format="%.2f days")
        elif raw == "average_review_score": config[label] = st.column_config.NumberColumn(label, format="%.2f")
        elif raw in {"orders", "unique_customers", "reviews", "eligible_orders"}: config[label] = st.column_config.NumberColumn(label, format="%d")
    return config


def _render_answer(answer, message_id):
    st.markdown(answer.message)
    render_answer_chart(answer, message_id)
    if len(answer.data) > 1:
        st.dataframe(prepare_display_table(answer.data), use_container_width=True, hide_index=True, height=min(390, 40 + 35 * len(answer.data)), column_config=_table_config(answer), key=assistant_element_key(answer, message_id, "table"))
    st.caption(f"Scope: {answer.scope} · {answer.evidence.row_count} verified rows · {answer.evidence.execution_ms:.0f} ms")
    response_label = str(message_id).rsplit("-", 1)[-1]
    with st.expander(f"View query & evidence · Response {response_label}", expanded=False):
        metadata = answer.metadata
        direction = humanize_label(metadata.ranking_direction) if metadata.ranking_direction != "none" else "Not applicable"
        st.markdown(
            f"**Interpreted intent:** {answer.interpretation}  \n"
            f"**Requested metric:** {humanize_label(metadata.metric)}  \n"
            f"**Dimension:** {humanize_label(metadata.dimension)}  \n"
            f"**Ranking direction:** {direction}  \n"
            f"**Effective scope:** {answer.evidence.effective_scope}  \n"
            f"**Verified rows:** {answer.evidence.row_count}  \n"
            f"**Metric definition:** {answer.evidence.metric_definition}  \n"
            f"**Source:** {answer.evidence.source}"
        )
        st.code(answer.sql, language="sql", wrap_lines=True)
        for warning in answer.warnings:
            st.info(warning)


def _render_error(message, filters):
    kind = message.get("kind", "execution")
    if kind in {"unsupported", "causal", "no_data"}: st.info(message["error"])
    elif kind == "security": st.error(message["error"])
    else: st.warning(message["error"])
    if message.get("retryable"):
        label = f"Retry: {message['question'][:64]}{'…' if len(message['question']) > 64 else ''}"
        if st.button(label, key=f"assistant_retry_{message['id']}", disabled=bool(st.session_state.get("assistant_submission_in_progress"))):
            if _submit(message["question"], filters): st.rerun()


def _submit(question, filters) -> bool:
    clean = str(question or "").strip()
    if not clean or st.session_state.get("assistant_submission_in_progress", False):
        return False
    st.session_state.setdefault("assistant_messages", [])
    st.session_state["assistant_submission_in_progress"] = True
    st.session_state["assistant_last_submission"] = clean
    st.session_state["assistant_message_sequence"] = int(st.session_state.get("assistant_message_sequence", 0)) + 1
    sequence = st.session_state.assistant_message_sequence
    message_id = f"response-{sequence}"
    append_message(st.session_state.assistant_messages, {"role": "user", "content": clean, "id": f"user-{sequence}"})
    try:
        with st.spinner("Analyzing your question..."):
            answer = ask_assistant(clean, filters, use_llm=True)
        append_message(st.session_state.assistant_messages, {"role": "assistant", "answer": answer, "id": message_id})
    except AssistantError as exc:
        status = friendly_status(exc)
        append_message(st.session_state.assistant_messages, {"role": "assistant", "error": status.message, "kind": status.kind, "id": message_id, "question": clean, "retryable": status.retryable})
    except Exception:
        status = friendly_status(Exception())
        append_message(st.session_state.assistant_messages, {"role": "assistant", "error": status.message, "kind": status.kind, "id": message_id, "question": clean, "retryable": False})
    finally:
        st.session_state["assistant_submission_in_progress"] = False
    return True


def render(filters) -> None:
    st.session_state.setdefault("assistant_messages", [])
    st.session_state.setdefault("assistant_submission_in_progress", False)
    page_header("InsightFlow AI Business Analyst", "Governed conversational analytics backed only by verified PostgreSQL results.", "Read-Only Analyst")
    filter_context(filters.start_date, filters.end_date, filters.states, filters.categories)
    configured = AISettings.from_environment() is not None
    status_col, clear_col = st.columns([5, 1])
    with status_col:
        status_badge("Governed provider configured" if configured else "Provider configuration required", "success" if configured else "warning")
    with clear_col:
        if st.button("Clear chat", disabled=not bool(st.session_state.assistant_messages), use_container_width=True, key="assistant_clear_chat"):
            clear_conversation_state(st.session_state)
            st.rerun()

    history_empty = not st.session_state.assistant_messages
    if history_empty:
        st.markdown("""
            <div class="if-assistant-hero"><div class="if-assistant-orb">✦</div><div>
            <div class="if-assistant-kicker">GOVERNED BUSINESS ANALYST</div>
            <div class="if-assistant-title">Ask a verified business question</div>
            <div class="if-assistant-copy">Explore sales, customers, products, sellers, delivery, reviews, and payments using governed read-only analytics.</div>
            </div></div>""", unsafe_allow_html=True)
        if not configured:
            st.warning("AI planning is not configured. Your dashboard remains available, but Assistant questions require provider configuration.")
        st.markdown("#### Suggested questions")
        columns = st.columns(3)
        for index, prompt in enumerate(SUGGESTED_QUESTIONS):
            with columns[index % 3]:
                if st.button(f"✦  {prompt}", disabled=not configured, use_container_width=True, key=f"assistant_prompt_{index}"):
                    if _submit(prompt, filters): st.rerun()

    for index, message in enumerate(st.session_state.assistant_messages):
        with st.chat_message(message["role"]):
            if message["role"] == "user": st.markdown(message["content"])
            elif "answer" in message: _render_answer(message["answer"], message.get("id", f"legacy-{index}"))
            else: _render_error(message, filters)

    if configured:
        question = st.chat_input("Ask about revenue, customers, categories, delivery, reviews, sellers, or payments", disabled=bool(st.session_state.get("assistant_submission_in_progress")))
        if question and _submit(question, filters): st.rerun()
    else:
        st.text_input("Ask a question about your business data", placeholder="Provider configuration is required", disabled=True)
    st.caption("Read-only governance · approved analytics only · maximum 100 rows · 10-second SQL timeout · no arbitrary Python")
