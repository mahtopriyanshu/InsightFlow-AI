# Milestone 19 — Governed AI Business Analyst

## Purpose

The InsightFlow AI Business Analyst converts a business question into a bounded, approved analytics intent, deterministic SQL, a structurally validated read-only PostgreSQL query, and a concise explanation based only on verified result rows. It does not allow arbitrary SQL, arbitrary Python, direct credential access, model-calculated KPIs, or unsupported factual answers.

## Architecture

```text
Business question + active dashboard filters
                     ↓
       Adversarial / unsupported precheck
                     ↓
    One provider call → approved intent plan
                     ↓
     Semantic allowlist and scope validation
                     ↓
       Deterministic parameterized SQL
                     ↓
 sqlglot structural validator + policy limits
                     ↓
 Dedicated read-only PostgreSQL connection
                     ↓
     Result shape and row-count validation
                     ↓
 Deterministic explanation and chart selection
                     ↓
 Answer + effective scope + query/evidence
```

The LLM never receives database credentials and never executes SQL. It returns only an approved JSON intent plan. SQL comes exclusively from reviewed application templates.

## Package structure

`streamlit_app/assistant/` separates:

- typed question, plan, evidence, and answer models;
- semantic definitions and allowlists;
- provider configuration and planning;
- deterministic SQL templates;
- structural SQL validation;
- dedicated read-only execution;
- result validation;
- deterministic result formatting;
- bounded chart rendering;
- cached end-to-end orchestration.

## Semantic layer

Approved metric definitions include:

| Metric | Definition |
|---|---|
| Payment revenue | Sum of validated order payment revenue |
| Merchandise revenue | Sum of `order_items.price` |
| Orders | Distinct `order_id` count |
| Unique customers | Distinct `customer_unique_id` count |
| AOV | Payment revenue divided by distinct orders |
| Delivery rate | Delivered orders divided by filtered orders |
| Late-delivery rate | Late eligible deliveries divided by eligible deliveries |
| Average review score | Mean order review score in scope |
| Negative-review rate | Share of review rows scored 1–2 |
| Payment usage | Distinct orders and payment value by payment method |

Approved dimensions are month, customer destination state, product category, seller, and payment method. Payment and merchandise revenue remain explicitly different.

### Governed monthly capability matrix

The semantic layer validates a metric × dimension × time-grain × intent-type ×
chart-type combination before SQL generation. The approved monthly trend shape
is `month`, `month`, `line`, and no ranking direction. Supported metrics are:

| Metric | Canonical monthly definition | Display unit |
|---|---|---|
| Payment revenue | Sum of validated order payment revenue by purchase month | R$ |
| Orders | Distinct orders by purchase month | count |
| Average order value | Payment revenue / distinct orders by purchase month | R$ |
| Unique customers | Distinct `customer_unique_id` by purchase month | count |
| Delivery rate | Delivered orders / filtered orders by purchase month | % |
| Late-delivery rate | Late eligible deliveries / eligible deliveries by purchase month | % |
| Average delivery days | Mean recorded actual-delivery duration by purchase month | days |
| Average review score | Mean order review score by review-creation month within the filtered order scope | score |
| Negative-review rate | Reviews scored 1–2 / review rows by review-creation month within scope | % |

Trend language—including “monthly,” “month by month,” “over time,” and “trend
by month”—returns the complete chronological series. Highest/lowest-month
questions remain separate one-row ranking intents. Multi-metric monthly trends
and category × month analysis remain intentionally unsupported because the
current governed model approves one primary metric and one primary dimension
per query.

Boundary months are included because filters represent an exact requested
scope. They may therefore be partial. Evidence and the deterministic formatter
state this explicitly; boundary values are not classified as unexplained
collapses. Review trends retain the existing review-creation-month convention
while the active order filters still define the eligible order scope.

## Allowed database objects

Assistant SQL can reference only approved objects in `olist_analytics`:

- `orders`
- `customers`
- `order_items`
- `products`
- `product_category_translation`
- `order_payments`
- `order_reviews`
- `sellers`
- `vw_order_revenue`
- `vw_order_delivery_metrics`
- `mv_order_revenue`

The existing M10 view-first `filtered_orders_cte` remains the serving path and retains its validated fallback behavior.

## SQL security model

Defense in depth includes:

1. The model returns an intent plan, not SQL.
2. SQL templates are parameterized and reviewed.
3. `sqlglot` parses the complete PostgreSQL statement.
4. Exactly one statement must resolve to `SELECT` / safe `WITH…SELECT`.
5. Tables, schema, and referenced columns are allowlisted.
6. `SELECT *`, comments, multiple statements, Cartesian joins, excessive joins, unsafe functions, and system catalogs are rejected.
7. Write and administrative operations—including INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, COPY, CALL, MERGE, REFRESH, VACUUM, ANALYZE, REINDEX, GRANT, and REVOKE—are rejected.
8. The dedicated PostgreSQL connection sets `default_transaction_read_only=on` and a 10-second statement timeout.
9. Results are capped at 100 rows.

Blocked functions include file access, large-object import/export, directory inspection, external database links, and configuration/secret inspection functions.

## Query limits

- Maximum returned rows: 100
- Default ranking limit: 10
- Maximum user-requested ranking limit: 25
- SQL statement timeout: 10 seconds
- Maximum joins: 14, including serving CTE joins
- Category review ranking: minimum 30 reviews
- Late-delivery state ranking: minimum 100 eligible deliveries
- No arbitrary detail-table extraction

## Provider configuration and role

The provider architecture supports Google Gemini and preserves the earlier OpenAI-compatible adapter. Both use the Python standard library, so no large SDK is required. Configuration is environment-only. Gemini is the default when `AI_PROVIDER` is omitted and an `AI_API_KEY` is present:

```dotenv
AI_API_KEY=...
AI_PROVIDER=gemini
AI_MODEL=gemini-3.1-flash-lite
AI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
```

Gemini uses the official `generateContent` REST endpoint, sends the key only in the `x-goog-api-key` header, and requests an intent object constrained by a response schema. The schema limits `intent` to the approved semantic intents plus `unsupported`; it does not contain an SQL field.

The API key is never rendered, logged, added to prompts, hardcoded, modified, or passed to PostgreSQL. One provider call interprets each uncached question. The business explanation is deterministic from verified rows, so no second explanation call is required.

The local Gemini key was validated with one harmless planning request. The returned plan mapped “What are the top 5 categories by revenue?” to `top_categories` with limit 5 and no scope override. No SQL or database query was involved in that provider test. When the key is absent, the page still renders a professional unavailable state and executes no assistant query. The golden suite uses the deterministic validation planner so database correctness tests remain repeatable and independent of API availability.

## Filter behavior

The provider receives only the approved semantic context and active date/state/category scope. Active filters apply by default. Explicit question scope overrides only the dimension it names—for example, “Compare SP and RJ” overrides an active destination-state selection but preserves the active date and category.

Every answer displays its complete effective date range plus destination-state and category scope. Unknown states/categories are rejected before query execution.

## Supported questions

The approved intents cover:

- total payment revenue, orders, unique customers, and AOV;
- top merchandise-revenue categories and sellers;
- top payment-revenue destination states;
- monthly payment-revenue trend and peak order month;
- payment-method distribution;
- delivery and late-delivery rates;
- average and negative review metrics;
- qualifying category review ranking;
- qualifying late-delivery state ranking;
- SP/RJ-style destination-state revenue comparison.

## Unsupported questions

Requests for inventory, carriers/delivery companies, future viral products, individual customer causality, guaranteed churn, credentials, environment variables, unsupported fields, or arbitrary write/admin SQL return a concise unsupported or blocked response. The system does not use causality language or invent missing data.

## Chart rules

Charts are chosen deterministically from verified result shape and approved intent:

- single metric → KPI-style answer;
- monthly series → line chart;
- rankings and comparisons → horizontal bar chart;
- bounded payment distribution → donut;
- result evidence → governed table.

No LLM-generated Python or visualization code is executed.

Ranking plans also carry explicit, allowlisted metadata: requested metric,
dimension, chart type, ranking direction, limit, and optional time grain. The
semantic layer canonicalizes provider output against the original question, so
the renderer never guesses a primary metric from dataframe column order. For
example, category orders uses `category` / `orders`, while category merchandise
revenue uses `category` / `merchandise_revenue`. `top`, `highest`, `most`, and
`best` map to descending order; `bottom`, `lowest`, and `least` map to ascending
order. Formatter wording follows that validated direction and remains
descriptive.

Every assistant Plotly chart and result table receives a deterministic SHA-256
based Streamlit key. The digest uses non-secret intent metadata plus the unique
conversation response instance. Repeating an identical cached question can
therefore render multiple history entries without duplicate element IDs; API
keys, credentials, SQL parameters, and raw result values are never included in
the key.

## Conversation and failure handling

Streamlit session state keeps conversation entries append-only. Unsupported,
blocked, empty-result, and provider-failed requests are appended as ordinary
assistant outcomes and never clear earlier messages. Provider failures are
typed separately from semantic rejections and expose an explicit Retry button;
retry performs no call until the user clicks it. A future Clear Chat action can
explicitly remove history, but no implicit pruning currently occurs. Unlimited
history is never sent to the model: only the current question and active
semantic scope are provided. Errors remain sanitized without credentials,
provider internals, SQL-driver details, stack traces, or environment values.

Questions phrased as causal “why/because/what caused” requests are rejected
with guidance to ask for a comparison or observed contributors. M19 does not
silently turn a causal question into a KPI or chart and never states that an
observed association proves causality.

## Testing

Focused tests cover golden intent mapping, explicit/active scope precedence,
limit bounds, requested metric propagation, ascending/descending ranking,
chart-axis selection, chronological trends, repeated-chart widget keys,
table/column allowlists, `SELECT *`, comments, multi-statements, write SQL,
catalogs, Cartesian joins, unsafe functions, excessive limits, adversarial
prompts, legitimate wording, and unsupported inventory requests.

Live validation reconciles 15 golden questions against existing validated services and tests full history plus six required filtered combinations. It also confirms `transaction_read_only=on`, a 100-row result ceiling, parameterized SQL, and cached response behavior.

## Performance and cost

The live 15-question golden suite completed in approximately 24.7 seconds. Individual validated revenue SQL executions across tested scopes were approximately 121–369 ms. A repeated cached full-scope answer returned in approximately 1 ms. Each uncached configured question uses one provider call; cached questions use none.

## Limitations

- Gemini model availability and free-tier quotas can change; provider failures return a sanitized unavailable state.
- Natural-language coverage is intentionally narrower than unrestricted text-to-SQL.
- Category reviews use an order-review experience attribution and are not direct product sentiment or seller ratings.
- The assistant does not perform forecasting beyond implemented M18 targets, causal inference, recommendations, or external-data analysis.
- M20 is not implemented.
