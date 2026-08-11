# Milestone 14 — Anomaly & Opportunity Detection

## Definitions

An anomaly is a completed-period observation that is both materially different from its trailing historical baseline and outside robust historical variation. An opportunity is the same statistical condition in a direction considered favorable for that metric. Neither is a forecast, causal explanation, recommendation, or machine-learning prediction.

## Architecture

```text
Historical Analytics
        ↓
Robust Baseline
        ↓
Deviation Detection
        ↓
Guardrails
        ↓
Typed Alert / Opportunity
        ↓
Priority
        ↓
Alerts Center
        ↓
Evidence
```

PostgreSQL supplies cached monthly aggregates. The anomaly layer contains typed `Alert` and `AlertEvidence` objects, robust baseline utilities, the detector, rules/configuration, and a coordinating engine. Page renderers only request and display typed alerts.

## Metrics covered

- Commercial: payment revenue, orders, AOV.
- Customer: unique customers, monthly repeat rate, revenue per customer.
- Delivery: delivery rate, late-delivery rate, average delivery days.
- Reviews: average score, negative-review rate, one-star rate, five-star rate.
- Categories: merchandise revenue, orders, average review score for the eight highest-exposure categories.
- Sellers: merchandise revenue, orders, late-delivery rate for the eight highest-exposure sellers.

Product/category revenue remains merchandise revenue; executive revenue remains validated payment revenue.

## Robust baseline formula

For each observation, only prior values are used. The trailing window is the previous eight completed periods, requiring at least six.

```text
baseline = median(previous 8 observations)
MAD = median(|x - baseline|)
robust scale = max(1.4826 × MAD, IQR / 1.349)
robust z = (observed - baseline) / robust scale
```

An alert requires `|robust z| ≥ 3.5` plus a metric-specific minimum magnitude. When historical scale is exactly zero, an unchanged value is safe; a material non-zero deviation is treated as outside the zero-variation baseline. This handles repeated equal values without division errors.

## History and partial periods

The Olist database spans 25 calendar months, but the reliable complete-month window is February 2017 through August 2018. A month is eligible only when selected data covers calendar day 1 through the month's final day. September and October 2018 are excluded, as are incomplete early boundary months. A narrow selected analysis range still receives prior same-scope history from the dataset start; only alerts inside the selected range are shown.

Entity series require six prior active observations. Missing entity months are not imputed and therefore cannot be mistaken for zero revenue. This is conservative for intermittent sellers/categories.

## False-positive controls

- Minimum six prior periods and eight-period bounded baseline.
- Robust z threshold 3.5.
- Minimum relative changes: revenue/orders/customers 15%, AOV/value 10%, entity merchandise revenue 20%.
- Minimum absolute changes: rates 2–5 percentage points, review score 0.25 points, delivery time 1.5 days.
- Business months require at least 100 orders/reviews/eligible deliveries as appropriate.
- Categories require at least 25 monthly orders; category reviews require at least 100 monthly reviews.
- Sellers require at least 20 monthly orders/eligible deliveries.
- Only eight highest-exposure categories and sellers receive routine entity detection.
- Commercial category opportunities are suppressed when the same period has a detected review deterioration.
- Commercial seller opportunities are suppressed when the same period has detected late-delivery deterioration.
- Visible alerts are capped at eight executive and five page-level items.

## Severity and priority

Favorable deviations are `positive` opportunities. Unfavorable deviations are warnings. `critical` requires robust z at least 6.0 and at least twice the configured sample threshold. Priority combines deviation magnitude, unfavorable impact, and sample reliability through transparent fixed rules; most recent qualifying alerts sort first, then priority.

## Evidence model

Every card exposes:

- observed value;
- trailing baseline;
- relative or point deviation;
- period and entity;
- rolling median/MAD/IQR method;
- number of historical periods;
- detector threshold and observed robust z;
- sample size;
- active state/category/date scope.

## Filter semantics

State and category filters are retained while historical dates are extended backward for the baseline. Customer state means destination-market scope. Category history retains item-level Product Pro semantics. Seller entity identity and location remain seller-based even when customer destination state filters the qualifying orders.

## Real Olist findings

The final full-scope executive detector identified:

- November 2017: unusually elevated late-delivery rate and average delivery days.
- December 2017: elevated delivery time and negative-review rate.
- January 2018: unusual positive order and unique-customer volume.
- February and March 2018: unusually elevated late-delivery rates.

Major-category signals included unusually strong `computers_accessories` order and merchandise revenue in January–February 2018, plus November 2017 growth signals across several major categories. Major-seller results included a July 2018 merchandise-revenue drop for seller `4869f7a5…` and multiple high-sample late-delivery anomalies during November 2017–March 2018. These results describe historical deviations; they do not explain causes.

## Performance

Cold full-scope executive detection measured 4.44 seconds, including its PostgreSQL historical aggregation. Repeating the already cached scope measured 0.46 seconds for the detector pass. Historical query outputs are cached for 300 seconds. Detection is bounded to monthly executive metrics and eight major categories/sellers; it does not scan 32,951 products individually.

## Limitations

- The dataset provides only 19 reliably complete consecutive months, limiting seasonal interpretation.
- No year-over-year seasonal model is claimed.
- Entity histories use active observations rather than imputing missing months.
- Historical signals do not establish cause or future direction.
- Category opportunities only screen for detected review deterioration; they are not recommendations.
- Seller review anomaly detection is omitted because M13 seller reviews are shared order-experience proxies.
- State-level delivery anomaly detection is deferred because the initial implementation prioritizes stable executive/category/seller series and avoids multiplying query cost.
