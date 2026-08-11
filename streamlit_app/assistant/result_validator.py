"""Validate verified query output before presentation."""
import numpy as np
import pandas as pd
from streamlit_app.assistant.models import AssistantError, NoDataError


def validate_result(frame: pd.DataFrame) -> None:
    if len(frame) > 100:
        raise AssistantError("The result exceeded the governed row limit.")
    if frame.empty:
        raise NoDataError("No verified rows matched the effective scope.")
    if any(str(column).startswith("?") for column in frame.columns):
        raise AssistantError("The result schema could not be validated.")
