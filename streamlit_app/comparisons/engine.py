"""Construct typed comparisons and deterministic observations."""
from streamlit_app.comparisons.metrics import compare_metric
from streamlit_app.comparisons.models import ComparisonEvidence,ComparisonResult

def build_result(mode,left_label,right_label,left,right,specs,scope,left_sample=None,right_sample=None):
    metrics=[]
    for name,key,dtype,unit,direction,definition in specs:
        evidence=ComparisonEvidence(definition,left_sample,right_sample,scope)
        metrics.append(compare_metric(name,key,left.get(key),right.get(key),dtype,unit,direction,evidence))
    observations=[]
    for metric in metrics:
        if not metric.available:continue
        d=metric.difference
        if metric.difference_type=="percent":label=f"{abs(d):.1f}%"
        elif metric.difference_type=="percentage_points":label=f"{abs(d):.1f} percentage points"
        elif metric.difference_type=="days":label=f"{abs(d):.1f} days"
        elif metric.difference_type=="points":label=f"{abs(d):.2f} points"
        else:label=f"{abs(d):,.0f}"
        relation="higher" if d>0 else "lower" if d<0 else "equal"
        observations.append(f"{left_label} has {label} {relation} {metric.name.lower()} than {right_label}." if d else f"{metric.name} is equal for {left_label} and {right_label}.")
    prioritized=sorted(observations,key=lambda text:("Revenue" not in text,"Late" not in text))[:5]
    return ComparisonResult(mode,left_label,right_label,tuple(metrics),tuple(prioritized),scope)
