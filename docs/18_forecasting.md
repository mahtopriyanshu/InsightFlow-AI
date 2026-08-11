# Milestone 18 — Validated Revenue & Order Forecasting

## Purpose and scope

Milestone 18 adds conservative, filter-aware forecasts for monthly **payment revenue** and **distinct orders**. Forecasts are model estimates rather than facts. Merchandise revenue is not mixed into the executive revenue target, and no forecast changes the historical M17 health score.

## Architecture

```text
PostgreSQL serving layer / validated fallback
                  ↓
        Same-scope monthly history
                  ↓
 Global completed-month calendar
                  ↓
  Leakage-safe preparation and guardrails
                  ↓
 Expanding-window candidate backtests
                  ↓
 Objective model selection per target
                  ↓
  Three-month forecast + residual band
                  ↓
       Opt-in Sales forecast workspace
```

The modular implementation is under `streamlit_app/forecasting/`: data preparation, feature construction, model adapters, error metrics, backtesting, and orchestration remain separate from Streamlit presentation.

## Historical data audit

The live full-business audit identified **19 completed monthly periods**, from February 2017 through August 2018. Completeness is recalculated from live unfiltered dataset coverage. Partial January 2017 and trailing partial September/October 2018 activity are not treated as collapses.

Filtered categories and states need not transact on the first or last day of a month. Therefore, calendar completeness is established using global dataset coverage, while metric values retain the active state/category scope. A scoped month with no matching orders is preserved as a real zero-volume period rather than silently removed.

## Targets

- Revenue: validated monthly payment revenue from the existing executive serving path.
- Orders: monthly count of distinct filtered orders.

Only completed months are used for training, validation, and forecasts.

## Candidate models

Each eligible target independently evaluates:

1. Naive last-observation forecast.
2. Drift from the first to the latest training observation.
3. Linear regression over a sequential time index.
4. Holt exponential smoothing with level and additive trend, without seasonality.
5. Random Forest using lag 1–3, prior three-period rolling mean/standard deviation, calendar month, quarter, and sequential index.

All Random Forest features available at an origin are derived only from observations before the predicted period. Future Random Forest forecasts are recursive. XGBoost was omitted because the available monthly history is small and the existing mandatory candidates already cover simple, statistical, and tree-based approaches without adding another dependency. Holt-Winters seasonality, Prophet, deep learning, and long-horizon models were intentionally omitted because fewer than two reliable annual cycles are available.

## Chronological validation

The engine uses expanding-window one-month-ahead backtesting:

```text
train 1..9  → predict 10
train 1..10 → predict 11
...
train 1..18 → predict 19
```

There is no random train/test split. All candidates use comparable forecast origins. Full-scope evaluation contains ten out-of-sample origins.

## Metrics and selection

For every candidate the engine calculates:

- MAE — mean absolute error;
- RMSE — root mean squared error;
- WAPE — total absolute error divided by total absolute actual value.

WAPE is unavailable when the actual denominator is zero. Models are ranked by lowest WAPE, then MAE, then RMSE. Revenue and Orders are selected independently. Machine-learning models receive no preference.

### Full-scope validation

| Revenue model | MAE | RMSE | WAPE |
|---|---:|---:|---:|
| Random Forest (selected) | R$130,823.38 | R$190,507.10 | 12.15% |
| Naive | R$148,283.26 | R$198,051.71 | 13.77% |
| Holt | R$158,100.86 | R$185,236.94 | 14.68% |
| Drift | R$167,000.14 | R$208,316.74 | 15.51% |
| Linear Trend | R$172,318.98 | R$203,754.83 | 16.00% |

| Orders model | MAE | RMSE | WAPE |
|---|---:|---:|---:|
| Random Forest (selected) | 785.99 | 1,240.03 | 11.69% |
| Naive | 879.30 | 1,253.00 | 13.08% |
| Holt | 968.12 | 1,180.53 | 14.40% |
| Drift | 974.98 | 1,310.28 | 14.51% |
| Linear Trend | 1,222.94 | 1,384.74 | 18.20% |

Different filtered scopes selected Linear Trend or Holt when those models achieved lower validation error, demonstrating that model selection is scope- and evidence-dependent.

## Horizon and forecast values

The forecast horizon is limited to three months because the completed history is short. For the full-business scope, the selected models produced:

| Future month | Revenue forecast | Orders forecast |
|---|---:|---:|
| September 2018 | R$1,098,383.57 | 6,576.63 |
| October 2018 | R$1,081,176.66 | 6,496.70 |
| November 2018 | R$1,086,311.88 | 6,496.56 |

These values are estimates, not reconstructed actuals.

## Uncertainty

For a selected model, the engine calculates the 90th percentile of its absolute walk-forward residuals. The displayed approximate band is:

```text
forecast ± 90th percentile absolute validation residual
```

The lower bound is clipped at zero. This is a transparent empirical validation-error band, not a native probabilistic confidence interval and not a guarantee. It is omitted when fewer than five residuals are available.

## Filter guardrails

Forecast history respects customer destination state and product category. The date-filter end determines the last eligible historical month; earlier history is retained for the baseline window. A forecast is unavailable when:

- fewer than 12 completed monthly periods exist;
- median monthly volume is below 25 orders;
- the scoped dataset is empty or otherwise cannot produce eligible model results.

The UI displays the reason instead of fabricating a forecast.

## UI and caching

Sales Analytics contains an opt-in **Validated Forecasting** workspace. It displays next-month estimates, selected models, WAPE, horizon, actual history, walk-forward predictions, future forecasts, uncertainty bands, model-performance tables, and selection rationale.

Forecasting is disabled by default so ordinary Sales reruns do not train models. Historical queries and complete forecast reports use Streamlit caches keyed by the immutable filter state with a five-minute TTL.

Live validation measured a full-scope cold execution of approximately 10.51 seconds in the standalone validation process and a cached call of approximately 0.002 seconds. Filtered cold executions ranged from approximately 4.14 to 6.58 seconds after shared metadata/history caches were warm.

## Validation and limitations

Focused tests cover completed-period construction, partial-month exclusion, missing/zero periods, leakage-safe lags and rolling features, chronological origins, MAE/RMSE/WAPE, zero denominators, ranking, insufficient history, low-volume filters, empty scopes, and horizon safety.

Limitations:

- Nineteen complete months provide limited evidence and insufficient annual cycles for seasonal modeling.
- Random Forest feature importance is intentionally not presented as causal explanation.
- Residual bands are approximate and can understate structural uncertainty.
- Forecasts do not incorporate external economic, promotional, inventory, or marketplace events absent from the schema.
- Longer-horizon forecasts are intentionally unavailable.
