"""Typed anomaly and opportunity objects."""
from dataclasses import dataclass
from typing import Literal

Severity=Literal["informational","positive","warning","critical"]
Direction=Literal["positive","negative","high","low"]
Category=Literal["anomaly","warning","opportunity"]

@dataclass(frozen=True)
class AlertEvidence:
    observed:str
    baseline:str
    deviation:str
    detector_method:str
    historical_periods:int
    threshold:str
    sample_size:int|None=None

@dataclass(frozen=True)
class Alert:
    title:str;message:str;metric:str;entity_type:str;entity_label:str;period:str
    observed_value:float;baseline_value:float;deviation:float;severity:Severity
    direction:Direction;category:Category;evidence:AlertEvidence;scope:str
    priority:float;detector_method:str="Rolling median + MAD"
