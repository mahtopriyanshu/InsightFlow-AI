# Milestone 13 — Product & Seller Intelligence Pro

## Metric grain and attribution

### Product and category

Item economics are aggregated from one `order_items` row per order item. `SUM(price)` is explicitly labelled **merchandise revenue** and never mixed with payment revenue. Units are item rows; orders and products are distinct identifiers. Freight is `SUM(freight_value)` and freight burden is freight divided by merchandise revenue.

Reviews are deduplicated to one `review_id` per category or product before aggregation. Delivery is deduplicated to one order–category or order–product row. This prevents item quantity from multiplying order-level reviews and delivery outcomes.

### Seller

Seller economics use one order-item row attributed to its `seller_id`; orders are distinct. Reviews are an **order-level experience proxy**, attributed once to each seller represented in the reviewed order. This is defensible for marketplace experience monitoring but is not a direct seller rating. Delivery is attributed once per order–seller. The audit found 1,278 multi-seller orders, so this deduplication is mandatory.

All three independent merchandise paths reconcile to **R$13,591,643.70**, 112,650 units, 32,951 products, and 3,095 sellers for full history.

## Concentration and Pareto

Entities are ranked by merchandise revenue. Cumulative shares and the first entity share reaching 80% are calculated from actual results.

| Analysis | Entities generating 80% | Other concentration |
|---|---:|---:|
| Categories | 24.32% | Top 5: 39.74%; Top 10: 62.36% |
| Products | 25.91% | Top 10%: 60.85% |
| Sellers | 17.58% | Top 10 sellers: 13.15%; Top 10%: 67.56% |

No 80/20 outcome is assumed.

## Commercial versus experience matrix

Category matrix axes are merchandise revenue and average review score; bubble size is distinct orders. Reference lines use median qualifying-category revenue and the review-count-weighted average review score. Seller matrix uses seller merchandise revenue and late-delivery rate, with qualifying medians as reference lines and order volume as bubble size. These are descriptive associations, not causal claims.

## Deterministic signals

- **Experience Risk:** at/above median category revenue with below-benchmark reviews.
- **Fulfillment Watch:** qualifying high-order category or meaningful-revenue seller with above-median late rate.
- **Freight Watch:** freight ratio above 1.5× the qualifying-category median.
- **Opportunity Signal:** above-benchmark reviews and meaningful demand with below-median category revenue.
- **Operational Risk Signal:** upper-quartile qualifying seller revenue with above-median late rate.

Full-data examples include `agro_industry_and_commerce` and `fixed_telephony` as experience investigation signals. `books_general_interest`, `food`, and `drinks` meet the opportunity-signal rule. These are investigation signals, not recommendations.

## Freight intelligence

Only categories with at least 25 orders and 25 reviews enter comparison signals. The highest full-data qualifying ratios include `flowers` (44.04%), `furniture_mattress_and_upholstery` (37.33%), and `christmas_supplies` (36.69%). The dashboard always shows the qualifying median alongside the leader rather than calling freight inherently excessive.

## Seller geography and cross-intelligence

Seller geography uses `seller_state`; customer-state filtering remains destination-market context. SP contains 1,849 represented sellers and R$8.75M in full-data seller merchandise revenue, followed by PR and MG.

Category/seller concentration aggregates seller merchandise revenue inside each category and reports seller count, top-seller share, and top-five-seller share. The UI emphasizes major categories (at or above median category revenue) so tiny categories are not overinterpreted.

## Sample thresholds

Live distributions informed the guardrails:

- Category comparisons: at least 25 orders and 25 reviews. The live category median is 246 orders and 244 reviews.
- Product comparisons: at least 10 orders, corresponding approximately to the product-order 95th percentile.
- Seller fulfillment comparisons: at least 20 orders, close to the seller-order upper quartile (21.5).
- Seller-state strategic interpretation: at least five sellers where a state threshold is required.

## Filter semantics

Date and customer state filter the qualifying orders. Customer state always means destination market. Product category filters are additionally enforced at item level in the new Product/Seller Pro services, preventing unrelated items in mixed-category orders from entering category-scoped merchandise totals. Seller geography continues to use the seller's own state and city.

## Performance decisions

PostgreSQL performs all item, review, delivery, and seller aggregation. Only entity-level results are transferred: 74 categories, 32,951 products, and 3,095 sellers for full history. Results are cached for 300 seconds. No new view, materialized view, or index was created because the measured cold queries complete within the existing 30-second safeguard and schema creation was unnecessary.

Measured cold full-data service timings were 4.42 seconds for categories, 4.56 seconds for products, 3.62 seconds for sellers, and 0.44 seconds for category/seller concentration. The final headless pages rendered in 10.53 seconds for Product Intelligence and 4.07 seconds for Seller Intelligence; subsequent identical filter runs use the 300-second cache.

## Architecture

```text
Orders + Items + Products + Sellers
              ↓
     Validated aggregations
              ↓
    Product / Seller metrics
       ↓                 ↓
Contribution         Fulfillment
Pareto               Concentration
Experience           Risk signals
       ↓                 ↓
       M11 Insight Engine
              ↓
Product & Seller Intelligence UI
```

## Limitations and no-causality policy

- Seller reviews are shared order-experience proxies when an order contains multiple sellers.
- Review, delivery, and commercial relationships do not prove causation.
- Signals identify relative conditions for investigation; they are not failure predictions or recommendations.
- Product-level review and delivery metrics can remain sparse even after order deduplication.
- Category filters in these modules use item-level scope; older non-product dashboards retain their validated order-scope definitions.
