# Milestone 23 — Portfolio and Final Release

## Project Story

### Problem

The Olist marketplace dataset spans orders, customers, products, sellers, items, payments, delivery timestamps, reviews, geography, and category translation. Useful business questions cross several of those grains, making naive joins vulnerable to duplicated revenue, inflated review counts, inconsistent customer identity, and misleading comparisons. The project needed to become more than a dashboard: it needed a traceable analytical system that could support business intelligence, forecasting, and natural-language questions safely.

### Approach

InsightFlow AI was built incrementally from dataset inventory and EDA through validated ETL, relational modeling, reusable SQL, a Streamlit application, deterministic intelligence, forecasting, governed AI, production readiness, cloud deployment, and CI quality gates. Each capability preserves filter scope and metric definitions, and the implementation separates data preparation, database serving, domain services, intelligence logic, UI presentation, and AI governance.

### Architecture

Nine immutable Olist CSV sources feed a Python ETL pipeline that validates schemas, keys, relationships, and reconciliations before loading PostgreSQL. The `olist_analytics` schema stores curated relational tables, a materialized one-row-per-order revenue object, and stable revenue/delivery views. Cached Python services provide metrics to a nine-page Streamlit application deployed on Render against Neon PostgreSQL.

GitHub is the source of truth. Credential-free GitHub Actions gates compile validity, repository safety, and 90 deterministic tests. Render owns Git-backed auto-deployment; Neon provides managed PostgreSQL over SSL/TLS; Gemini provides constrained structured planning for the Assistant.

### Analytics and Intelligence

The application covers executive, sales, customer, product, seller, delivery, review, and report workflows. RFM segmentation and Pareto analysis support customer-value exploration. Product/Seller modules connect merchandise economics to freight, reviews, fulfillment, and concentration. Robust rolling median and MAD/IQR baselines identify unusual completed-period movements. Compare Mode evaluates periods and entities, Explain KPI decomposes observed changes descriptively, and Business Health combines transparent component scores with evidence-backed risks, opportunities, and recommendations.

### Governed AI

The AI Business Analyst deliberately limits the model's authority. Gemini maps a question and active filters to an approved plan; the application validates semantic metadata, generates parameterized SQL deterministically, validates the query with sqlglot and explicit allowlists, executes through bounded read-only PostgreSQL, verifies the result, and formats the answer/chart/evidence without asking the model to invent conclusions. Unsupported, causal, unsafe, provider, timeout, and no-data outcomes remain distinct. Production validation confirmed the Render → Gemini → Neon path with a monthly revenue trend request.

### Forecasting

Revenue and order forecasts compare Naive, Drift, Linear Trend, Holt Exponential Smoothing, and Random Forest candidates. Expanding-window one-step-ahead backtesting prevents random temporal leakage, WAPE determines the selected model, and MAE/RMSE remain visible evidence. Forecasts use complete periods, a three-month horizon, nonnegative outputs, empirical residual bands, and history/volume guardrails.

### Production, Testing, and Security

The live application runs on Render with Neon PostgreSQL and Gemini configuration supplied through protected environment variables. Production health, core rendering, critical database objects/counts, SSL/TLS, and the governed Assistant path passed M21 validation.

Testing evolved from focused domain tests to database reconciliation, headless Streamlit interaction, golden Assistant questions, security/adversarial cases, provider failure, and production smoke checks. The current pull-request CI gate runs 90 deterministic tests without external credentials. Historical validated evidence includes 106/106 unit tests, 38/38 focused Assistant tests, 15/15 golden questions, 14/14 Assistant UX checks, and all nine pages rendering without exceptions.

Secrets remain environment-driven and ignored. CI blocks tracked environment files, Streamlit secrets, credential notes, and database dumps. Assistant execution is read-only, parameterized, structurally validated, limited to approved semantics, capped at 100 rows, and subject to a 10-second statement timeout. Operational errors avoid credential values and raw connection strings.

## Major Engineering Challenges

1. **Preventing grain multiplication:** payment, item, review, and delivery facts required separate aggregation/deduplication rules. The serving layer and service queries make grain explicit rather than relying on broad joins.
2. **Keeping explanations honest:** Compare, Explain, and Assistant wording distinguishes observed drivers and relationships from unsupported causal claims.
3. **Governing natural-language analytics:** the model was constrained to planning, while deterministic application code retained SQL generation, validation, execution, and presentation authority.
4. **Forecasting with limited history:** chronological backtesting, simple model competition, completed periods, and volume/history guardrails were prioritized over overstated sophistication.
5. **Production performance:** Product Intelligence profiling isolated PostgreSQL-heavy work and removed an unnecessary full business-history query, reducing comparable cold render time from 15.58 seconds to 7.52 seconds without changing analytical output.
6. **Credential-free CI:** database-dependent scope tests were isolated with deterministic filter fixtures so pull-request tests pass with no PostgreSQL or Gemini configuration.

## Final Outcome

InsightFlow AI is a complete portfolio system rather than a collection of notebooks: governed data engineering, reusable analytics, interactive decision support, explainable intelligence, cautious forecasting, constrained AI, production deployment, and automated quality gates are connected in one traceable architecture. M23 changes presentation and release preparation only; working application and production infrastructure remain unchanged.

## Interview Preparation

### 30-second project explanation

InsightFlow AI is a production-deployed e-commerce intelligence platform I built on the Olist dataset. I created a validated Python-to-PostgreSQL pipeline, nine Streamlit analytics workspaces, RFM and portfolio intelligence, explainable comparisons and health scoring, five-model time-series forecasting, and a governed Gemini assistant. The assistant cannot execute arbitrary SQL—it only plans approved intents, while application code generates and validates bounded read-only queries. The app runs on Render with Neon PostgreSQL and is protected by credential-free GitHub Actions quality gates.

### 60–90 second project explanation

I started with nine related Olist CSV files and focused on the hardest analytical problem: preserving grain across orders, payments, items, reviews, customers, products, and sellers. A validated ETL pipeline loads a constrained `olist_analytics` PostgreSQL schema, and a materialized order-revenue layer prevents fan-out in repeated analytics. On top of that I built a nine-page Streamlit product with global filters, RFM segmentation, Product/Seller intelligence, robust anomaly detection, comparisons, descriptive KPI decomposition, Business Health recommendations, exports, and three-month revenue/order forecasts selected through expanding-window WAPE backtesting. For natural language, Gemini returns only a structured approved plan; deterministic code generates parameterized SQL, sqlglot enforces allowlists and read-only bounds, and verified results drive the answer and chart. The production stack is GitHub, GitHub Actions, Render, Neon, and Gemini, with 90 credential-free CI tests plus database, UI, security, and production validation outside ordinary pull-request CI.

### Three resume bullets

- Engineered and production-deployed an end-to-end e-commerce intelligence platform using Python, Streamlit, PostgreSQL/Neon, Plotly, Render, and GitHub Actions, spanning validated ETL, nine analytical workspaces, exports, and managed cloud delivery.
- Built explainable customer, product, seller, anomaly, comparison, Business Health, and forecasting workflows, including RFM/Pareto analysis and five-model expanding-window backtesting with WAPE-based selection and explicit reliability guardrails.
- Designed a governed Gemini analytics assistant that converts filter-aware questions into allowlisted plans, deterministic parameterized SQL, sqlglot validation, bounded read-only PostgreSQL execution, and verified answer/chart/evidence output; protected changes with 90 credential-free deterministic CI tests.

## v1.0.0 Release Preparation

### Proposed release

- **Version:** `v1.0.0`
- **Recommended title:** `InsightFlow AI v1.0.0 — Production E-Commerce Intelligence Platform`

### Readiness checklist

- [x] Production application health and core dashboard validated
- [x] Neon schema, critical relations, representative counts, and SSL/TLS validated
- [x] Governed Render → Gemini → Neon Assistant request validated
- [x] Credential-free GitHub Actions CI passing 90/90 focused tests
- [x] Repository secret/export safety gate present
- [x] Portfolio README, architecture, project story, and screenshot plan prepared
- [ ] Capture, review, optimize, and add selected real screenshots
- [ ] Review the final tracked diff and confirm no unrelated files
- [ ] Confirm the latest `main` CI run passes after documentation merge
- [ ] Perform one final manual production health/core-page smoke against the release commit
- [ ] Confirm the Render deployment is serving the intended release commit
- [ ] Create annotated `v1.0.0` tag and GitHub Release manually

### Before tagging

Do not tag until real screenshots have been reviewed, CI passes on the exact release commit, the production health endpoint returns `ok`, the core dashboard renders, and the deployed commit matches the intended source revision. Repeat the repository safety gate and inspect release notes for credentials or private URLs.

### Draft release notes

```markdown
## InsightFlow AI v1.0.0

InsightFlow AI is a production-deployed e-commerce intelligence platform built on the Olist marketplace dataset.

### Highlights
- Nine Streamlit analytics and intelligence workspaces
- Governed PostgreSQL analytics serving layer on Neon
- Customer RFM, Product/Seller intelligence, anomaly detection, Compare/Explain, and Business Health
- Three-month revenue and order forecasting selected by expanding-window validation
- Governed Gemini Business Analyst with allowlisted deterministic SQL and read-only execution
- Filter-aware CSV and Excel reporting
- Render production deployment and credential-free GitHub Actions CI

### Validation
- 90/90 focused deterministic CI tests
- Production health, core application, Neon database, and governed AI path validated
- Repository safety gates block tracked secrets and database exports

### Notes
The Olist data is historical and anonymized. Forecasts and observational driver analysis are decision-support tools, not guarantees or causal proof.
```

The tag and GitHub Release are intentionally not created during M23.
