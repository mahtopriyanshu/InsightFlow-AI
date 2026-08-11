"""Typed models for interactive verified comparisons."""
from dataclasses import dataclass,field
from typing import Literal

DifferenceType=Literal["percent","percentage_points","days","points","absolute","unavailable"]

@dataclass(frozen=True)
class ComparisonEvidence:
    metric_definition:str;left_sample:int|None;right_sample:int|None;scope:str;source:str="Validated PostgreSQL analytics"

@dataclass(frozen=True)
class ComparisonMetric:
    name:str;key:str;left_value:float|None;right_value:float|None;difference:float|None
    difference_type:DifferenceType;unit:str;preferred_direction:Literal["higher","lower","neutral"]
    evidence:ComparisonEvidence;available:bool=True

@dataclass(frozen=True)
class ComparisonResult:
    mode:str;left_label:str;right_label:str;metrics:tuple[ComparisonMetric,...]
    observations:tuple[str,...]=field(default_factory=tuple);scope:str="Selected filters";available:bool=True;reason:str|None=None
