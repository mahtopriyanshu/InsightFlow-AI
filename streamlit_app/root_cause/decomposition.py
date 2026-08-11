"""Mathematically exact two-factor revenue decomposition."""
def revenue_decomposition(current_orders,current_aov,previous_orders,previous_aov):
    """Symmetric/Shapley decomposition of Revenue = Orders × AOV."""
    values=[float(x) for x in (current_orders,current_aov,previous_orders,previous_aov)]
    o1,a1,o0,a0=values
    volume=(o1-o0)*(a1+a0)/2
    aov=(a1-a0)*(o1+o0)/2
    total=o1*a1-o0*a0
    return {"volume":volume,"aov":aov,"total":total,"reconciliation_error":total-volume-aov}
