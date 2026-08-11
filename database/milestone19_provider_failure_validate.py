"""Headless provider-failure UX validation without exposing provider details."""
import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def main():
    original = os.environ.get("AI_BASE_URL")
    os.environ["AI_BASE_URL"] = "http://127.0.0.1:1"
    try:
        app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"), default_timeout=180).run()
        assistant = next(page for page in app.sidebar.radio[0].options if "AI Assistant" in page)
        app.sidebar.radio[0].set_value(assistant).run(timeout=180)
        app.chat_input[0].set_value("Show monthly orders.").run(timeout=180)
        assert not app.exception
        assert len(app.session_state["assistant_messages"]) == 2
        retry = [button for button in app.button if button.label.startswith("Retry:")]
        assert len(retry) == 1
        assert any("temporarily unavailable" in str(item.value) for item in app.warning)
        print({"provider_failure": "distinct", "history_messages": 2, "retry_buttons": 1, "automatic_retry": False})
    finally:
        if original is None:
            os.environ.pop("AI_BASE_URL", None)
        else:
            os.environ["AI_BASE_URL"] = original


if __name__ == "__main__":
    main()
