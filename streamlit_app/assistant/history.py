"""Append-only Assistant conversation state helpers."""


def append_message(history: list[dict], message: dict) -> None:
    """Append one message without implicit pruning or replacement.

    Conversation history may only be removed by an explicit future user action.
    Provider, semantic, security, no-data, and execution failures are messages,
    not reset conditions.
    """
    history.append(message)


CONVERSATION_KEYS = {
    "assistant_messages",
    "assistant_message_sequence",
    "assistant_submission_in_progress",
    "assistant_last_submission",
    "assistant_retry_in_progress",
}
CONVERSATION_WIDGET_PREFIXES = ("assistant_chart_", "assistant_table_", "assistant_retry_")


def clear_conversation_state(state) -> None:
    """Clear only Assistant conversation and its transient widget state."""
    keys = list(state.keys())
    for key in keys:
        if key in CONVERSATION_KEYS or str(key).startswith(CONVERSATION_WIDGET_PREFIXES):
            state.pop(key, None)
    state["assistant_messages"] = []
    state["assistant_message_sequence"] = 0
    state["assistant_submission_in_progress"] = False
