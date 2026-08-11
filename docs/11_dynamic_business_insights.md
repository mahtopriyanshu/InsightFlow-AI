# Milestone 11 — Dynamic Business Insight Engine

## Architecture

```text
PostgreSQL
    ↓
Analytics Services (view-first, CTE fallback)
    ↓
Verified Metrics
    ↓
Comparable-Period and Delta Engine
    ↓
Deterministic Domain Rules
    ↓
Typed Insight + Evidence Objects
    ↓
Streamlit Insight Cards
```

The engine is deterministic. It does not call an LLM, generate SQL, infer
causality, or create recommendations.

## Package structure

- `insights/models.py` — typed `Insight` and `Evidence` dataclasses.
- `insights/comparisons.py` — comparable periods and safe deltas.
- `insights/config.py` — documented thresholds and card limits.
- `insights/engine.py` — executive, sales, customer, product, seller,
  delivery, and review rules.
- `components/layout.py` — shared severity-aware cards and evidence display.

Pages pass already-loaded current metrics to the engine. Previous-period
metrics are requested only when the dataset contains a complete comparable
period. Existing service caching prevents duplicate work during a rerun.

## Previous comparable period

The selected range is inclusive. Its duration is:

```text
duration = end_date - start_date + 1 day
previous_end = start_date - 1 day
previous_start = previous_end - duration + 1 day
```

State and category filters are copied to the previous period. If
`previous_start` predates the dataset, comparison is marked unavailable and
no growth claim is emitted. Single-day selections compare with the immediately
preceding day.

## Delta rules

- **Absolute change:** `current - previous`
- **Percentage change:** `(current - previous) / abs(previous) × 100`
- **Percentage-point change:** `current_rate - previous_rate`

Percentage change is unavailable when the previous value is zero. `None`,
NaN, infinity, empty frames, and invalid ranges are rejected safely.

Revenue, orders, customers, AOV, and revenue/customer use percentage change.
Delivery, late-delivery, repeat-customer, and negative-review rates use
percentage points. Review scores use score points; delivery duration uses days.

## Sample guardrails

Configured in `insights/config.py`:

| Comparison | Minimum sample |
|---|---:|
| State delivery ranking | 100 eligible deliveries |
| Seller fulfillment ranking | 20 orders |
| Category review ranking | 25 reviews |
| Delivery/review relationship | 100 reviews per compared outcome |

If no group qualifies, that ranking or relationship insight is omitted.

## Severity rules

- General percentage movements smaller than 2% are neutral.
- Favorable movements of at least 2% are positive.
- Adverse movements of at least 2% are warnings.
- Adverse rate changes of at least 1 percentage point are warnings.
- Adverse rate changes of at least 3 percentage points are critical.
- Review-score movements require at least 0.10 points.
- Delivery-time movements require at least 0.50 days.

Critical is therefore reserved for a documented rate deterioration threshold;
leaders and concentration observations remain informational.

## Prioritization

Each rule has a transparent base priority reflecting business relevance:

1. operational risk and delivery/review association;
2. revenue, order, and customer movement;
3. magnitude of a validated change;
4. revenue/customer concentration and leaders;
5. descriptive mix observations.

Magnitude adds a bounded priority increment. Executive Overview shows at most
six insights; other pages show at most five. No machine learning is involved.

## Filter awareness

Every insight receives the active `FilterState`. Current and comparison
queries retain the selected state and category. Evidence stores the current
period, comparison period, sample size, scope, and PostgreSQL source label.

Examples of scope values:

- `All selected marketplace data`
- `state: SP`
- `category: health_beauty`
- `state: SP · category: health_beauty`

## Evidence and trust

Every emitted insight contains an `Evidence` object. The UI provides a compact
**View evidence** expander with:

- current value;
- previous value, when available;
- difference and correct unit;
- current and comparison periods;
- qualifying sample size;
- active filter scope;
- source label.

## Domain coverage

- **Executive:** revenue, orders, AOV, customers, delivery, reviews, category,
  state, payment, and customer mix.
- **Sales:** revenue/orders/AOV movement, peak month, category/state leaders,
  and payment concentration.
- **Customers:** customer and revenue/customer movement, repeat-rate points,
  customer mix, geography, and highest-value customer.
- **Products:** revenue/order leaders, category share, qualifying review
  leaders/watch, and freight burden.
- **Sellers:** revenue/order leaders, displayed-set concentration, geography,
  and fulfillment guardrails. No seller rating is invented.
- **Delivery:** delivery and late-rate points, delivery days, on-time mix, and
  qualifying state rankings.
- **Reviews:** score and negative-rate movement, five-star share, qualifying
  category rankings, and delivery/review association.

Association wording is deliberate. The engine never says delivery performance
causes review outcomes.

## Limitations

- Full-history selections cannot have a preceding equal-duration period, so
  they show current-period leaders and mix rather than fabricated growth.
- Comparisons are descriptive and are not statistical significance tests.
- Seller concentration describes the displayed ranked seller set because the
  page service intentionally limits that dataset.
- Category revenue is merchandise revenue; executive/state revenue is payment
  revenue, preserving existing validated definitions.
- No recommendation, forecasting, anomaly detection, RFM, or AI capability is
  included.
