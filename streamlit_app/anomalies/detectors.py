"""Explainable robust time-series anomaly detector."""
import math
import pandas as pd

from streamlit_app.anomalies.baselines import rolling_baselines
from streamlit_app.anomalies.config import CRITICAL_Z_THRESHOLD,METRIC_RULES,ROBUST_Z_THRESHOLD
from streamlit_app.anomalies.models import Alert,AlertEvidence
from streamlit_app.insights.comparisons import scope_label
from streamlit_app.utils.formatting import currency,number,percentage

def _format(value,kind):
    if kind=="currency":return currency(value)
    if kind=="percentage":return percentage(value)
    if kind=="days":return f"{number(value,1)} days"
    if kind=="score":return f"{number(value,2)} / 5"
    return number(value)

def detect_series(frame:pd.DataFrame,metric:str,filters,*,entity_type="business",entity_label="All business",sample_column:str|None=None,min_sample:int=0)->list[Alert]:
    """Detect sufficiently large deviations from a trailing robust baseline."""
    if frame.empty or metric not in frame:return []
    data=frame.copy();base=rolling_baselines(data[metric]);data=pd.concat([data,base],axis=1)
    rule=METRIC_RULES[metric];alerts=[]
    for _,row in data.iterrows():
        observed=pd.to_numeric(pd.Series([row[metric]]),errors="coerce").iloc[0]
        baseline=row.baseline
        if pd.isna(observed) or pd.isna(baseline):continue
        sample=int(row[sample_column]) if sample_column and pd.notna(row.get(sample_column)) else None
        if sample is not None and sample<min_sample:continue
        deviation=float(observed-baseline);relative=100*deviation/abs(baseline) if baseline else None
        scale=max(float(row.mad)*1.4826,float(row.iqr)/1.349 if row.iqr else 0)
        if scale>0:z=deviation/scale
        elif deviation==0:z=0
        else:z=math.copysign(float("inf"),deviation)
        magnitude_ok=abs(deviation)>=rule.get("absolute",0) and (relative is None or abs(relative)>=rule.get("relative",0))
        if abs(z)<ROBUST_Z_THRESHOLD or not magnitude_ok:continue
        favorable=(deviation>0 and rule["favorable"]=="high") or (deviation<0 and rule["favorable"]=="low")
        category="opportunity" if favorable else "anomaly";severity="positive" if favorable else ("critical" if abs(z)>=CRITICAL_Z_THRESHOLD and sample is not None and sample>=min_sample*2 else "warning")
        period=pd.Timestamp(row["month"]).strftime("%b %Y");direction="positive" if favorable else "negative"
        deviation_text=f"{relative:+.1f}%" if "relative" in rule and relative is not None else f"{deviation:+.2f} points"
        title=f"{metric.replace('_',' ').title()} {'Opportunity' if favorable else 'Anomaly'}"
        message=f"{metric.replace('_',' ').title()} in {period} is {deviation_text} versus its trailing robust baseline."
        threshold=f"|robust z| ≥ {ROBUST_Z_THRESHOLD:.1f}; observed {abs(z):.1f}"
        alerts.append(Alert(title,message,metric,entity_type,entity_label,period,float(observed),float(baseline),float(z),severity,direction,category,AlertEvidence(_format(observed,rule['format']),_format(baseline,rule['format']),deviation_text,"Trailing rolling median + MAD/IQR",int(row.history_periods),threshold,sample),scope_label(filters),min(100,55+abs(z)*5+(20 if not favorable else 10))))
    return alerts
