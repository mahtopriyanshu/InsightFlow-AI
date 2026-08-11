# Milestone 16 — Explain KPI / Observed Driver Analysis

## Purpose and language policy

M16 explains which observed factors contributed to a comparable-period difference. It does not identify proven root causes. Output uses `contributed`, `associated`, `observed movement`, `exposure`, and `coincided`; it avoids `caused` and `because of`.

## Architecture

```text
Selected period + previous equal-duration period
                 ↓
         Validated KPI snapshots
                 ↓
     Exact decomposition / dimension changes
                 ↓
       Typed DriverAnalysis / DriverEvidence
                 ↓
        Contribution chart + evidence
```

## Revenue decomposition

For payment revenue `R = Orders × AOV`, the engine uses a symmetric two-factor Shapley decomposition:

```text
Volume contribution = (O1 - O0) × (A1 + A0) / 2
AOV contribution    = (A1 - A0) × (O1 + O0) / 2
```

The two contributions reconcile exactly to `O1×A1 - O0×A0`. This avoids interaction double counting. The live January–March 2018 analysis reconciled R$461,632.02 within floating-point tolerance.

## Analyses

- **Revenue:** exact order-volume/AOV decomposition; additive payment-revenue destination-state drivers; separately labelled merchandise category and seller exposure.
- **Orders:** category exposure and additive destination-state changes. Category order counts can overlap and are not forced to sum to the total.
- **Delivery:** qualifying destination-state late-rate differences with at least 100 delivered orders.
- **Reviews:** review-score distribution movement and the existing late-versus-on-time review association. No delivery causality claim.
- **Customers:** destination-state unique-customer movement, repeat-rate context, and explicit reminder that RFM At Risk is historical behavior—not churn prediction.

## Contribution methodology

For additive dimensions, entity change is `current - previous`. Contribution percentage is only calculated when the total movement is materially non-zero. Positive offsets and negative drivers remain separate. Non-additive category exposure is labelled rather than forced to reconcile.

Driver queries are bounded to top absolute changes: five category/state drivers and three seller exposures. PostgreSQL performs aggregation and existing 300-second caches are reused.

## Evidence

Every driver includes current/comparison period, metric definition, scope, sample size where available, source, absolute movement, optional mathematically valid relative contribution, direction, and non-causal explanatory wording.

## Validation and limitations

Focused tests cover exact reconciliation, growth, decline, opposing orders/AOV movement, zero total change, offset contributors, missing dimensions, tiny samples, delivery units, review association wording, no-causality wording, and scope preservation. Live validation passed full/date/SP/category and combined contexts. Full-history analysis is unavailable because no equal-duration preceding period exists.

This is deterministic observational decomposition, not causal inference. Payment and merchandise revenue are intentionally not reconciled to one another. Product-level drivers are omitted from routine analysis to protect query performance.
