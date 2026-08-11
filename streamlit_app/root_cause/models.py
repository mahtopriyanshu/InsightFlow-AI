"""Typed observed-driver analysis models."""
from dataclasses import dataclass,field

@dataclass(frozen=True)
class DriverEvidence:
    current_period:str;comparison_period:str;metric_definition:str;scope:str;sample_size:int|None=None;source:str="Validated PostgreSQL analytics"
@dataclass(frozen=True)
class Driver:
    kpi:str;dimension:str;entity:str;current_value:float;comparison_value:float;absolute_contribution:float
    relative_contribution:float|None;direction:str;evidence:DriverEvidence;wording:str
@dataclass(frozen=True)
class DriverAnalysis:
    kpi:str;current_value:float;comparison_value:float;total_change:float;drivers:tuple[Driver,...]
    narrative:tuple[str,...]=field(default_factory=tuple);scope:str="Selected filters";available:bool=True;reason:str|None=None
