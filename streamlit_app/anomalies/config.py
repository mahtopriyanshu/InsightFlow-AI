"""Transparent anomaly history, magnitude, sample, and severity rules."""
MIN_HISTORY=6
ROLLING_WINDOW=8
ROBUST_Z_THRESHOLD=3.5
CRITICAL_Z_THRESHOLD=6.0
MIN_MONTHLY_ORDERS=100
MIN_MONTHLY_REVIEWS=100
MIN_CATEGORY_MONTHLY_ORDERS=25
MIN_SELLER_MONTHLY_ORDERS=20
MAX_EXECUTIVE_ALERTS=8
MAX_PAGE_ALERTS=5

METRIC_RULES={
 "revenue":{"relative":15.0,"favorable":"high","format":"currency"},
 "orders":{"relative":15.0,"favorable":"high","format":"number"},
 "average_order_value":{"relative":10.0,"favorable":"high","format":"currency"},
 "unique_customers":{"relative":15.0,"favorable":"high","format":"number"},
 "repeat_rate":{"absolute":2.0,"favorable":"high","format":"percentage"},
 "revenue_per_customer":{"relative":10.0,"favorable":"high","format":"currency"},
 "delivery_rate":{"absolute":3.0,"favorable":"high","format":"percentage"},
 "late_rate":{"absolute":3.0,"favorable":"low","format":"percentage"},
 "average_delivery_days":{"absolute":1.5,"favorable":"low","format":"days"},
 "average_review_score":{"absolute":.25,"favorable":"high","format":"score"},
 "negative_review_rate":{"absolute":3.0,"favorable":"low","format":"percentage"},
 "one_star_rate":{"absolute":3.0,"favorable":"low","format":"percentage"},
 "five_star_rate":{"absolute":5.0,"favorable":"high","format":"percentage"},
 "merchandise_revenue":{"relative":20.0,"favorable":"high","format":"currency"},
}
