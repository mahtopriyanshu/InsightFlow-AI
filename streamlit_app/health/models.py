"""Typed transparent business-health models."""
from dataclasses import dataclass,field

@dataclass(frozen=True)
class HealthComponent:
    name:str;metric:str;observed:float;benchmark:float;score:float;weight:float
    contribution:float;unit:str;reason:str;available:bool=True
@dataclass(frozen=True)
class HealthDimension:
    name:str;score:float|None;band:str;components:tuple[HealthComponent,...]
@dataclass(frozen=True)
class HealthEvidence:
    current_value:str;reference_value:str|None;period:str;sample_size:int|None;scope:str;source_module:str;reason:str
@dataclass(frozen=True)
class HealthSignal:
    title:str;message:str;kind:str;severity:str;metric:str;entity:str|None;evidence:HealthEvidence;priority:float
@dataclass(frozen=True)
class HealthReport:
    overall:HealthDimension;dimensions:tuple[HealthDimension,...];risks:tuple[HealthSignal,...];opportunities:tuple[HealthSignal,...];recommendations:tuple[HealthSignal,...]
