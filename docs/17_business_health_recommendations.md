# Milestone 17 — Business Health & Recommendation Center

## Purpose

Milestone 17 turns the existing validated analytics into a compact, deterministic executive decision-support layer. It answers how healthy the selected business scope appears, which evidence deserves attention, where positive signals exist, and what should be investigated next. It does not use machine learning, generative AI, causal inference, or hidden scoring.

## Architecture

```text
PostgreSQL serving views / validated CTE fallback
                    ↓
         Existing analytics services
                    ↓
       Current and historical metrics
                    ↓
     Transparent component scoring
                    ↓
 Four health dimensions + overall score
                    ↓
 M12/M13/M14 evidence-backed signals
                    ↓
 Executive Health & Recommendation Center
```

The engine is implemented in `streamlit_app/health/`. The presentation component is `streamlit_app/components/health_center.py`, and Executive Overview calls it from `streamlit_app/pages/overview.py`.

## Health dimensions

The engine calculates four dimensions and one overall score:

| Dimension | Available components |
|---|---|
| Revenue Health | Revenue, order, and AOV movement against a valid equal-duration period; when that comparison is unavailable, AOV against the same-scope completed-month historical norm |
| Customer Health | Revenue per customer and repeat-customer rate against same-scope completed-month norms |
| Fulfillment Health | Delivery rate, late-delivery rate, and average delivery days against same-scope completed-month norms |
| Satisfaction Health | Average review score, negative-review rate, and five-star share against same-scope completed-month norms |
| Overall Business Health | Equal-weight mean of available dimension scores |

Existing validated definitions are reused. Payment revenue remains the executive revenue definition. Product and seller merchandise revenue definitions are not substituted into executive scoring.

## Score methodology

Each available component receives a bounded score:

```text
component score = clip(
    50 + 25 × direction × (observed − benchmark) / tolerance,
    0,
    100
)
```

`direction` is `+1` when higher values are favorable and `-1` when lower values are favorable. Tolerance is the larger of the robust historical scale (`1.4826 × MAD`) and a documented minimum appropriate to the unit. This prevents a nearly constant series from creating extreme scores for immaterial changes.

Dimension scores are weighted means of their available components. When a component is unavailable, its weight is redistributed among available components. An unavailable comparison is never converted to a zero score.

The score bands are:

| Score | Band |
|---:|---|
| 85–100 | Excellent |
| 70–84.99 | Healthy |
| 55–69.99 | Watch |
| 40–54.99 | At Risk |
| 0–39.99 | Critical |

These bands describe the deterministic dashboard score, not future business outcomes.

## Evidence model

Every visible risk, opportunity, and recommended investigation carries:

- current value;
- reference or baseline when available;
- period;
- sample size when available;
- active filter scope;
- source analytical module;
- reason the item was flagged.

The UI exposes this through **View evidence** and **How are these scores calculated?** expanders.

## Risk and opportunity logic

Risks and opportunities reuse existing analytical modules instead of introducing competing definitions:

- M14 contributes statistically unusual risks and opportunities.
- M12 contributes RFM-based historical customer-value signals.
- M13 contributes qualifying product experience, fulfillment, and opportunity signals.

Visible signals are deterministically sorted by priority and capped to reduce clutter. An RFM `At Risk` label describes historical behavior and is not a churn prediction. Product and seller signals identify areas for investigation and are not forecasts or guaranteed opportunities.

## Recommendation guardrails

Recommendations are conservative investigation templates tied to a specific risk and its evidence. Approved language includes `Investigate`, `Review`, `Monitor`, and `Examine`. The engine does not prescribe budgets, pricing changes, staffing decisions, seller removal, or other actions that the data cannot support.

Recommendations inherit the triggering risk's metric, entity, period, sample, scope, and evidence. The engine avoids causal wording such as “caused” or “because of.”

## Filter semantics

All health metrics and signals respect the active:

- order-date range;
- customer destination state;
- product category;
- combined filter scope.

Historical benchmarks retain the same state/category scope and use completed months. If equal-duration comparison history is not available, the engine remains operational using available absolute and historical components.

## Validation

The focused health suite covers score bounds, favorable-direction handling, component reweighting, finite values, and missing-component behavior. The live validator covers full history, date, state, category, and all required combined scopes. It verifies bounded finite scores, evidence presence, filter-scope preservation, recommendation-to-risk mapping, and non-causal wording.

## Limitations

- Scores are relative analytical summaries, not universally calibrated financial ratings.
- Historical medians describe this dataset and should not be interpreted as external industry benchmarks.
- Sparse filtered scopes may have fewer available components or signals.
- RFM is descriptive; anomaly detection is historical; neither predicts future outcomes.
- Health scoring remains intentionally independent from forecasting.
