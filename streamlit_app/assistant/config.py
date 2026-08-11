"""Environment-only LLM provider configuration."""
from dataclasses import dataclass
import os

from streamlit_app.database.settings import PROJECT_ROOT  # ensures .env is loaded


@dataclass(frozen=True)
class AISettings:
    provider: str
    api_key: str
    model: str
    base_url: str

    @classmethod
    def from_environment(cls):
        key = os.getenv("AI_API_KEY", "").strip()
        if not key or key == "your_api_key_here":
            return None
        provider = os.getenv("AI_PROVIDER", "gemini").strip().lower()
        defaults = {
            "gemini": ("gemini-3.1-flash-lite", "https://generativelanguage.googleapis.com/v1beta"),
            "openai_compatible": ("", "https://api.openai.com/v1"),
        }
        if provider not in defaults:
            return None
        default_model, default_url = defaults[provider]
        model = os.getenv("AI_MODEL", default_model).strip()
        if not model or model == "your_model_name":
            return None
        return cls(provider, key, model, os.getenv("AI_BASE_URL", default_url).rstrip("/"))
