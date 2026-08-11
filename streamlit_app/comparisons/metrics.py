"""Safe unit-aware comparison calculations."""
import math
from streamlit_app.comparisons.models import ComparisonEvidence,ComparisonMetric

def safe_value(value):
    try:
        result=float(value)
        return result if math.isfinite(result) else None
    except (TypeError,ValueError):return None

def compare_metric(name,key,left,right,difference_type,unit,preferred_direction,evidence):
    left=safe_value(left);right=safe_value(right)
    if left is None or right is None:return ComparisonMetric(name,key,left,right,None,"unavailable",unit,preferred_direction,evidence,False)
    if difference_type=="percent":difference=None if right==0 else 100*(left-right)/abs(right)
    else:difference=left-right
    return ComparisonMetric(name,key,left,right,difference,difference_type if difference is not None else "unavailable",unit,preferred_direction,evidence,difference is not None)
