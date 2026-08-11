"""Documented health bands and minimum benchmark tolerances."""
BANDS=((85,"Excellent"),(70,"Healthy"),(55,"Watch"),(40,"At Risk"),(0,"Critical"))
MIN_TOLERANCE={"percent":10.0,"rate":3.0,"days":1.5,"score":.25,"currency":10.0}
def band(score):
    if score is None:return "Unavailable"
    return next(label for threshold,label in BANDS if score>=threshold)
