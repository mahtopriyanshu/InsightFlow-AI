# Milestone 20 — Production Readiness and Performance

## Scope

M20 audited the frozen M19 application for cloud portability, application-side performance, PostgreSQL and Gemini resilience, configuration, dependencies, safe operational logging, and deployment documentation. It added no analytics, KPIs, models, AI capabilities, database objects, or business-data changes.

## Audit Findings

### High value

1. **Product Intelligence cold rendering:** the baseline page render was approximately 15.58 seconds.
2. **Environment template mismatch:** `.env.example` documented `DATABASE_*` names while runtime settings require `DB_*`.
3. **Operational failure handling:** DB, provider, forecast, and page failures had incomplete logging; raw exception text could reach generic UI errors.
4. **Forecast isolation:** an unexpected forecast-service exception could replace the rest of Sales Analytics through the page-level handler.

### Low value — intentionally unchanged

- Broad replacement of Streamlit's deprecated `use_container_width` parameter. It is noisy on the installed future Streamlit version but does not affect current behavior; changing every page would be broad M9–M19 churn.
- Parallel query execution or a PostgreSQL connection pool. The current serialized reusable connection is predictable and safe; introducing concurrency would add connection-capacity and correctness risk.
- Consolidating the three grain-sensitive Product queries. Their category, product, review, and delivery deduplication rules differ, so forced consolidation risks metric drift.
- Removing Jupyter from `requirements.txt`. It is not required by the web process but remains legitimate for the repository's maintained notebooks.
- External logging, tracing, distributed caching, containers, and orchestration. These are outside M20.

## Product Intelligence Investigation

Cold component profiling showed:

| Component | Time |
|---|---:|
| Category analytics query | 3.097 s |
| Product analytics query | 3.470 s |
| Supplier concentration query | 0.301 s |
| Python concentration and signal processing | 0.118 s |
| Deterministic product insights | 0.011 s |
| Category anomaly history and detection | 3.909 s |

The dominant cost was PostgreSQL work, not dataframe processing or chart construction. Product analytics legitimately returns 32,951 product rows. Category anomalies also loaded the full multi-metric business history only to determine which scoped months were complete, then separately loaded category history.

### Optimization

For entity-only anomaly requests, the application now queries only monthly first/last order dates to identify complete months. Business-level alerts still use the existing full business-history query. Category history, detector rules, filters, prioritization, charts, tables, KPIs, and search are unchanged.

- Comparable before: **15.58 s**
- Comparable after: **7.52 s**
- Improvement: **8.06 s / approximately 51.7%**
- Rendered output after change: five charts, five dataframes, zero exceptions
- Old/new top-five Product alert signatures: equivalent

All existing five-minute Streamlit caches remain in place. Warm reruns reuse cached service results and do not repeat Gemini calls for successful identical Assistant requests.

## Configuration and Dependencies

- `.env.example` now uses the runtime `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` names.
- Gemini configuration remains environment-driven through `AI_API_KEY`, `AI_PROVIDER`, `AI_MODEL`, and `AI_BASE_URL`.
- `.env`, `.streamlit/secrets.toml`, and the removed credential-note path remain ignored.
- Runtime path discovery uses `Path(__file__)`; no required application path is tied to a developer checkout.
- The declared runtime dependencies cover Streamlit, Plotly, PostgreSQL, exports, forecasting, and governed SQL validation. No dependency was removed.
- `.streamlit/config.toml` contains presentation settings only and no secrets.

## Resilience Decisions

- PostgreSQL connection failures recreate the cached connection once. Health failures return a safe generic status instead of raw driver details.
- The application still stops at startup when PostgreSQL is unavailable because every page depends on the curated database; it fails visibly rather than partially rendering misleading analytics.
- Gemini/provider failures remain a distinct, retryable Assistant message. Retry is manual, exceptions are not cached, and there is no automatic provider retry loop.
- Successful identical Assistant requests remain cached by question, filters, and mode, avoiding unnecessary provider calls.
- Forecast-service failures are isolated to the forecast workspace so the rest of Sales Analytics remains usable.
- Page-level unexpected errors are logged by exception type and shown to users without raw exception details.

## Logging

Standard-library `logging` now records safe operational events for:

- PostgreSQL reconnection and health-check failure
- Gemini/provider request failure
- Forecast-service failure
- Unexpected page failure

Messages record operation and exception type only. They do not log API keys, passwords, environment values, SQL connection strings, provider payloads, or raw exception messages.

## Testing Performed

- Focused Product headless render: passed, zero exceptions
- Product alert before/after equivalence: passed
- Existing anomaly, portfolio, forecasting, and provider-resilience tests plus one new forecast-isolation test: **28/28 passed**
- Existing M18 forecast UI validator: required after the forecast workspace change
- Existing provider-failure validator: required after provider logging changes
- PostgreSQL health/read-only sanity and localhost Streamlit health endpoint
- Redacted secrets/ignore validation

The frozen full M9–M19 regression was intentionally not rerun.

## Remaining Deployment Prerequisites

M21 should select a cloud runtime and managed PostgreSQL target, provision secrets in the platform's secret manager, apply the validated schema/serving migration, load or restore the curated dataset, set network/TLS rules, configure the Streamlit start command and health check, size connection limits, and perform a deployment smoke test. No deployment was performed in M20.
