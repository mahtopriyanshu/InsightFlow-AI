# Milestone 12 — Customer Intelligence Pro / RFM

## Why RFM

RFM adds an explainable behavioral layer to the existing customer reporting without predicting churn or future lifetime value. It summarizes how recently a customer purchased, how many distinct orders they placed, and how much validated payment revenue they generated in the active filter scope.

## Customer identity and grain

The profile grain is `customer_unique_id`, not `customer_id`. In Olist, `customer_id` is an order-level customer record; 2,997 of the 96,096 stable customers map to more than one `customer_id` (maximum 17). Using `customer_id` would therefore understate repeat behavior. The live audit also found 39 stable identities recorded in multiple states and 122 in multiple cities; the dashboard uses the location attached to the customer's latest selected order.

## Definitions

- **Recency:** calendar days between the analytical reference date and the customer's latest selected purchase timestamp. Lower is better.
- **Frequency:** `COUNT(DISTINCT order_id)` per `customer_unique_id`. Order-item rows never count as purchases.
- **Monetary:** sum of `payment_revenue` from the validated M10 order-revenue serving view at customer grain. The join is order-to-order, so payments are not multiplied by item rows.
- **Order eligibility:** preserves the existing validated application meaning and includes the same selected orders/statuses as the other customer KPIs. No new status exclusion was silently introduced.

The full-data monetary total reconciles to **R$16,008,872.12**, the validated dashboard revenue. Three customer profiles have zero payment revenue.

## Reference date

The reference date is not today's date. It is one day after the earlier of:

1. the selected filter end date; and
2. the latest observed purchase date in the selected data.

For the full dataset this is **18 October 2018** (latest purchase + one day). This keeps recency aligned with historical and filtered analysis while avoiding artificial inactivity when a selected end date extends beyond available data.

## Live full-data distributions

| Metric | Count | Min | Q1 | Median | Mean | Q3 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|
| Recency (days) | 96,096 | 1 | 165 | 270 | 289.11 | 398 | 774 |
| Frequency (orders) | 96,096 | 1 | 1 | 1 | 1.0348 | 1 | 17 |
| Monetary (R$) | 96,096 | 0.00 | 63.12 | 108.00 | 166.59 | 183.53 | 13,664.08 |

Frequency is highly tied: 93,099 customers have one order, 2,745 have two, 203 have three, 30 have four, and 19 have five or more. Naive `qcut` would be unstable or misleading for this distribution.

## Scoring and ties

R and M use deterministic average-rank percentiles mapped to scores 1–5. Equal values receive the same percentile and therefore the same score. R is inverted so a lower recency receives a higher score. M is ascending so higher revenue receives a higher score.

F uses distribution-aware order bands:

| Distinct orders | F score |
|---:|---:|
| 1 | 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |
| 5+ | 5 |

These bands are transparent, reproducible, and preserve the meaningful distinction among the relatively few repeat buyers.

## Segment rules

Rules are evaluated in order, making the result mutually exclusive and exhaustive:

1. **Champions:** R ≥ 4, F ≥ 2, M ≥ 4.
2. **Loyal Customers:** F ≥ 3 and M ≥ 3.
3. **Potential Loyalists:** R ≥ 4 and F ≥ 2.
4. **Recent Customers:** R = 5 and F = 1.
5. **Promising:** R ≥ 4 and M ≥ 3.
6. **At Risk:** R ≤ 2 and either F ≥ 2 or M ≥ 4.
7. **Needs Attention:** R ≤ 3 and either F ≥ 2 or M ≥ 3.
8. **Hibernating:** all remaining qualifying profiles.

“At Risk” means inactive relative to this historical RFM distribution. It is not a churn prediction.

## Reconciliation and thresholds

Every qualifying customer receives exactly one segment. Segment customer counts reconcile to the selected unique-customer count; segment revenue reconciles to selected customer payment revenue within one cent. State/segment rankings require at least 25 customers. The customer value matrix uses an exact, deterministic, segment-balanced browser sample capped at 350 profiles per segment; all KPIs, Pareto values, insights, and tables use the complete profile population.

The validated full-data segment snapshot is:

| Segment | Customers | Customer share | Revenue (R$) | Revenue share |
|---|---:|---:|---:|---:|
| Champions | 1,068 | 1.11% | 408,056.52 | 2.55% |
| Loyal Customers | 115 | 0.12% | 51,834.32 | 0.32% |
| Potential Loyalists | 235 | 0.24% | 22,716.49 | 0.14% |
| Recent Customers | 18,594 | 19.35% | 3,069,723.43 | 19.18% |
| Promising | 11,312 | 11.77% | 2,683,550.95 | 16.76% |
| Needs Attention | 18,809 | 19.57% | 3,368,682.77 | 21.04% |
| At Risk | 15,174 | 15.79% | 4,703,018.51 | 29.38% |
| Hibernating | 30,789 | 32.04% | 1,701,289.13 | 10.63% |

## Filter semantics

- Date filters constrain purchases used by R, F, and M and determine the historical reference date.
- State filters constrain customers/orders to the selected customer state.
- Category filters select orders containing that category. Monetary retains the existing validated order-payment definition, so a mixed-category order contributes its full order payment, consistent with the rest of the application.
- Combined filters apply all rules together. No full-history RFM value is labeled as filtered data.

## Pareto methodology

Customers are sorted by selected-period monetary value, descending. The application calculates the cumulative customer share required to reach 80% of revenue and the exact revenue share generated by the top 10% of customers. It does not assume an 80/20 outcome. The displayed curve is deterministically thinned to at most 1,000 points; concentration metrics use all customers.

For the full dataset, **48.67% of customers generate 80% of revenue**, while the top 10% generate **38.51%**.

## Cohort feasibility

Cohort retention was evaluated and intentionally omitted. Only 2,997 customers (3.1188%) repeat, 2,149 purchase again on a later date, and later-month active counts fall from 461 at month one to 40 at month twelve. The limited repeat depth would make a retention heatmap visually elaborate but operationally weak.

## M11 integration

The existing typed `Insight` and `Evidence` architecture now receives exact RFM segment, Pareto, and guarded geography aggregates. It can report Champion contribution, historical At-Risk share, the customer share producing 80% of revenue, and the leading qualifying Champion state. Evidence includes period and sample size, and scope follows global filters.

## Architecture

```text
Orders + validated order revenue
              ↓
      customer_unique_id
              ↓
   Customer-level aggregation
              ↓
 Recency + Frequency + Monetary
              ↓
       R / F / M scores
              ↓
       Customer segment
              ↓
 Customer Intelligence dashboard
              ↓
    M11 dynamic insights
```

## Limitations

- RFM is descriptive historical segmentation, not machine learning, churn prediction, or future customer lifetime value.
- A category-filtered mixed-category order retains full validated payment revenue because payments cannot be allocated reliably to individual items.
- Sparse repeat behavior limits the size of high-frequency segments.
- Location is the latest selected order location and may differ from older order records.
- No database object was added; computation uses the M10 serving view and cached, bounded customer-level results.
