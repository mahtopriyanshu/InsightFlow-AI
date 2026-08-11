# Milestone 15 — Interactive Compare Mode

## Architecture

```text
Global filter context → comparison snapshot services → unit-aware metric engine
→ typed ComparisonResult / ComparisonMetric / ComparisonEvidence → Compare UI
```

Comparison business rules live under `streamlit_app/comparisons/`; PostgreSQL-backed snapshots remain in `services/comparisons.py`. The UI does not calculate metrics.

## Modes

1. **Period vs Period:** selected period versus the immediately preceding equal-duration period. Inclusive date boundaries are preserved. If the preceding range falls outside available history, the result is explicitly unavailable.
2. **Category vs Category:** two categories under active date and destination-state scope. The global category filter is intentionally removed so two categories can be selected. Merchandise metrics remain item-scoped, excluding unrelated mixed-order items.
3. **Destination State vs State:** two customer destination states under active date/category filters. These are never seller states.
4. **Seller vs Seller:** two active sellers under the selected order context. Seller geography remains seller-based. Review score is labelled `Order-level Experience Proxy` because multi-seller orders share reviews.

## Units and deltas

- Revenue/orders/customers/value: percent difference where the right denominator is non-zero.
- Delivery and review rates: percentage-point difference.
- Delivery duration: day difference.
- Review score: score-point difference.
- Zero denominator, null, NaN, or unsupported values produce an unavailable metric rather than a fabricated delta.

Preferred direction is metadata: higher revenue/orders is commercial advantage; lower late rate/delivery duration is operational advantage; ambiguous metrics remain neutral. The UI avoids universal better/worse claims.

## Evidence and filter scope

Each metric contains its definition, both sample sizes, comparison scope, and PostgreSQL source. Category revenue means merchandise revenue; period/state revenue means payment revenue.

## Performance and validation

Live seven-scope validation returned 10 period/state metrics, 11 category metrics, and 8 seller metrics. A cold January–March period comparison measured 0.84 seconds; repeated cached comparison measured 0.006 seconds. Full-history period comparison correctly returns unavailable because an equal-duration preceding range does not exist.

## Limitations

- Category order counts may overlap when orders contain multiple categories.
- Seller experience remains an order-level proxy.
- Comparison is descriptive and does not establish causality.
- Sellers are bounded to the top 100 active sellers in the interactive selector for responsiveness.
